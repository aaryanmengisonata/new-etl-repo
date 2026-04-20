from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

import pandas as pd

DataLike = Union[pd.DataFrame, Sequence[Mapping[str, Any]], Sequence[Sequence[Any]]]


class PredefinedValidations:
    """Reusable ETL validation helpers for source-target dataset comparison.

    All methods raise ``AssertionError`` with clear failure reasons so they can be
    used directly inside pytest test functions.
    """

    @staticmethod
    def _to_dataframe(
        data: DataLike,
        columns: Optional[Sequence[str]] = None,
        dataset_name: str = "dataset",
    ) -> pd.DataFrame:
        """Convert supported input types to a pandas DataFrame."""
        if isinstance(data, pd.DataFrame):
            return data.copy()

        if data is None:
            raise AssertionError(f"{dataset_name} is None; expected DataFrame-like input.")

        try:
            if columns is not None:
                return pd.DataFrame(data, columns=list(columns))
            return pd.DataFrame(data)
        except Exception as exc:  # pragma: no cover
            raise AssertionError(
                f"Unable to convert {dataset_name} to DataFrame: {exc}"
            ) from exc

    @staticmethod
    def _assert_columns_exist(df: pd.DataFrame, columns: Sequence[str], dataset_name: str) -> None:
        """Assert that required columns exist in a DataFrame."""
        missing = [col for col in columns if col not in df.columns]
        if missing:
            raise AssertionError(
                f"Missing columns in {dataset_name}: {missing}. Available: {list(df.columns)}"
            )

    @staticmethod
    def _normalize_series(series: pd.Series) -> pd.Series:
        """Normalize values for deterministic comparisons (NaN-safe, whitespace-safe, numeric-safe)."""

        # Try numeric conversion first
        numeric_series = pd.to_numeric(series, errors="coerce")

        # If conversion succeeded for most values, treat as numeric
        if numeric_series.notna().sum() >= len(series) * 0.8:
            return numeric_series

        # Datetime handling
        if pd.api.types.is_datetime64_any_dtype(series):
            return pd.to_datetime(series, errors="coerce")

        # Object handling
        if pd.api.types.is_object_dtype(series):
            return series.astype(str).str.strip()

        return series

    @staticmethod
    def row_count_comparison(source_data: DataLike, target_data: DataLike) -> Tuple[int, int]:
        """Validate total row count between source and target datasets."""
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        # Handle aggregate count queries (for example, SELECT COUNT(*)) that return
        # a single row where the cell values are the actual record counts.
        if (
            len(source_df) == 1
            and len(target_df) == 1
            and source_df.shape[1] == target_df.shape[1]
        ):
            source_numeric = source_df.apply(pd.to_numeric, errors="coerce")
            target_numeric = target_df.apply(pd.to_numeric, errors="coerce")

            if not source_numeric.isna().any().any() and not target_numeric.isna().any().any():
                source_values = source_numeric.iloc[0].tolist()
                target_values = target_numeric.iloc[0].tolist()

                mismatches: List[str] = []
                if list(source_df.columns) == list(target_df.columns):
                    for col, source_value, target_value in zip(
                        source_df.columns, source_values, target_values
                    ):
                        if int(source_value) != int(target_value):
                            mismatches.append(
                                f"{col}: source={int(source_value)}, target={int(target_value)}"
                            )
                else:
                    for idx, (source_value, target_value) in enumerate(
                        zip(source_values, target_values), start=1
                    ):
                        if int(source_value) != int(target_value):
                            mismatches.append(
                                f"col#{idx}: source={int(source_value)}, target={int(target_value)}"
                            )

                if mismatches:
                    raise AssertionError(
                        "Row count mismatch in aggregate query: "
                        + " | ".join(mismatches[:10])
                    )

                source_count = int(sum(source_values))
                target_count = int(sum(target_values))
                return source_count, target_count

        source_count = len(source_df)
        target_count = len(target_df)

        if source_count != target_count:
            raise AssertionError(
                f"Row count mismatch: source={source_count}, target={target_count}."
            )
        return source_count, target_count

    @staticmethod
    def column_count_validation(source_data: DataLike, target_data: DataLike) -> Tuple[int, int]:
        """Validate total number of columns between source and target datasets."""
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        source_cols = len(source_df.columns)
        target_cols = len(target_df.columns)

        if source_cols != target_cols:
            raise AssertionError(
                f"Column count mismatch: source={source_cols}, target={target_cols}."
            )
        return source_cols, target_cols

    @staticmethod
    def schema_and_datatype_validation(
        source_data: DataLike,
        target_data: DataLike,
        column_mapping: Optional[Mapping[str, str]] = None,
        strict_dtype_match: bool = False,
    ) -> Dict[str, str]:
        """Validate schema and datatype compatibility.

        Parameters
        ----------
        column_mapping:
            Mapping of source column -> target column. If None, same-name columns are used.
        strict_dtype_match:
            If True, requires exact dtype string match. If False, validates broad type families.
        """
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        mapping = dict(column_mapping or {col: col for col in source_df.columns})

        PredefinedValidations._assert_columns_exist(source_df, list(mapping.keys()), "source_data")
        PredefinedValidations._assert_columns_exist(target_df, list(mapping.values()), "target_data")

        mismatches: List[str] = []
        result: Dict[str, str] = {}

        for source_col, target_col in mapping.items():
            source_dtype = str(source_df[source_col].dtype)
            target_dtype = str(target_df[target_col].dtype)
            result[f"{source_col}->{target_col}"] = f"{source_dtype} vs {target_dtype}"

            if strict_dtype_match:
                if source_dtype != target_dtype:
                    mismatches.append(
                        f"{source_col}->{target_col}: source={source_dtype}, target={target_dtype}"
                    )
                continue

            source_is_num = pd.api.types.is_numeric_dtype(source_df[source_col])
            target_is_num = pd.api.types.is_numeric_dtype(target_df[target_col])
            source_is_dt = pd.api.types.is_datetime64_any_dtype(source_df[source_col])
            target_is_dt = pd.api.types.is_datetime64_any_dtype(target_df[target_col])
            source_is_bool = pd.api.types.is_bool_dtype(source_df[source_col])
            target_is_bool = pd.api.types.is_bool_dtype(target_df[target_col])

            compatible = (
                (source_is_num and target_is_num)
                or (source_is_dt and target_is_dt)
                or (source_is_bool and target_is_bool)
                or (
                    not source_is_num
                    and not target_is_num
                    and not source_is_dt
                    and not target_is_dt
                    and not source_is_bool
                    and not target_is_bool
                )
            )

            if not compatible:
                mismatches.append(
                    f"{source_col}->{target_col}: incompatible types source={source_dtype}, target={target_dtype}"
                )

        if mismatches:
            raise AssertionError("Schema/datatype validation failed: " + " | ".join(mismatches))

        return result

    @staticmethod
    def null_checks_mandatory_columns(
        data: DataLike,
        mandatory_columns: Sequence[str],
        treat_blank_as_null: bool = True,
    ) -> Dict[str, int]:
        """
        Validate mandatory columns do not contain NULL values.

        Enhancements:
        - Fails if dataset is empty
        - Optionally treats blank strings as NULL
        - Provides detailed failure message with row count
        """
        df = PredefinedValidations._to_dataframe(data, dataset_name="data")
        PredefinedValidations._assert_columns_exist(df, mandatory_columns, "data")

        if df.empty:
            raise AssertionError("Dataset is empty; cannot validate NULL constraints.")

        working_df = df.copy()

        if treat_blank_as_null:
            # Replace empty or whitespace-only strings with NA
            working_df[mandatory_columns] = working_df[mandatory_columns].replace(
                r'^\s*$', pd.NA, regex=True
            )

        null_counts = {
            col: int(working_df[col].isna().sum())
            for col in mandatory_columns
        }

        failing = {col: cnt for col, cnt in null_counts.items() if cnt > 0}
        
        total_rows = len(df)
        
        if failing:            
            raise AssertionError(
                f"Mandatory NULL check failed in {sum(failing.values())} cells "
                f"across {total_rows} rows. Column-wise NULL counts: {failing}"
            )

        return {
            "total_rows_verified": total_rows,
            "validated_columns": list(mandatory_columns),
            "null_counts": null_counts
        }


    @staticmethod
    def duplicate_checks_primary_keys(data: DataLike, primary_keys: Sequence[str]) -> int:
        """Validate no duplicate rows exist for provided primary key columns."""
        df = PredefinedValidations._to_dataframe(data, dataset_name="data")
        PredefinedValidations._assert_columns_exist(df, primary_keys, "data")

        duplicate_count = int(df.duplicated(subset=list(primary_keys), keep=False).sum())
        if duplicate_count > 0:
            raise AssertionError(
                f"Duplicate check failed: found {duplicate_count} duplicate rows on keys {list(primary_keys)}."
            )
        return duplicate_count

    @staticmethod
    def soft_delete_consistency(
        source_data: DataLike,
        target_data: DataLike,
        key_columns: Sequence[str],
        delete_column: str = "isdelete",
        max_mismatch_rows: int = 10,
    ) -> Dict[str, Any]:
        """Validate delete-flag consistency between source and target by business key."""
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        required_source_cols = list(key_columns) + [delete_column]
        required_target_cols = list(key_columns) + [delete_column]
        PredefinedValidations._assert_columns_exist(source_df, required_source_cols, "source_data")
        PredefinedValidations._assert_columns_exist(target_df, required_target_cols, "target_data")

        source_view = source_df[required_source_cols].copy()
        target_view = target_df[required_target_cols].copy()

        merge_df = source_view.merge(
            target_view,
            on=list(key_columns),
            how="inner",
            suffixes=("_source", "_target"),
        )

        source_col = f"{delete_column}_source"
        target_col = f"{delete_column}_target"
        left = pd.to_numeric(merge_df[source_col], errors="coerce")
        right = pd.to_numeric(merge_df[target_col], errors="coerce")
        mismatch_mask = ~(left.eq(right) | (left.isna() & right.isna()))

        mismatches = merge_df.loc[
            mismatch_mask, list(key_columns) + [source_col, target_col]
        ].head(max_mismatch_rows)

        summary = {
            "joined_row_count": int(len(merge_df)),
            "mismatch_count": int(mismatch_mask.sum()),
            "sample_mismatches": mismatches.to_dict(orient="records"),
        }

        if summary["mismatch_count"] > 0:
            raise AssertionError(f"Soft delete consistency failed: {summary}")

        return summary

    @staticmethod
    def aggregate_validations(
        source_data: DataLike,
        target_data: DataLike,
        aggregate_config: Mapping[str, Sequence[str]],
        tolerance: float = 0.0,
    ) -> Dict[str, Dict[str, float]]:
        """Validate aggregate metrics like SUM/MIN/MAX across datasets.

        Parameters
        ----------
        aggregate_config:
            Dict where key=column and value=list of aggregate names from {'sum','min','max'}.
        tolerance:
            Absolute tolerance applied to numeric aggregate comparisons.
        """
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        PredefinedValidations._assert_columns_exist(source_df, list(aggregate_config.keys()), "source_data")
        PredefinedValidations._assert_columns_exist(target_df, list(aggregate_config.keys()), "target_data")

        supported = {"sum", "min", "max"}
        results: Dict[str, Dict[str, float]] = {}
        failures: List[str] = []

        for column, aggs in aggregate_config.items():
            results[column] = {}
            for agg in aggs:
                agg_lower = agg.lower()
                if agg_lower not in supported:
                    raise AssertionError(
                        f"Unsupported aggregate '{agg}' for column '{column}'. Supported: {sorted(supported)}"
                    )

                source_value = float(getattr(source_df[column], agg_lower)())
                target_value = float(getattr(target_df[column], agg_lower)())
                results[column][agg_lower] = target_value

                if abs(source_value - target_value) > tolerance:
                    failures.append(
                        f"{column}.{agg_lower}: source={source_value}, target={target_value}, tolerance={tolerance}"
                    )

        if failures:
            raise AssertionError("Aggregate validation failed: " + " | ".join(failures))

        return results

    @staticmethod
    def record_level_dataframe_comparison(
        source_data: DataLike,
        target_data: DataLike,
        key_columns: Sequence[str],
        compare_columns: Optional[Sequence[str]] = None,
        max_mismatch_rows: int = 10,
    ) -> Dict[str, Any]:
        """Perform record-level comparison between source and target datasets.

        The method checks:
        1) Missing keys in target
        2) Extra keys in target
        3) Value mismatches on selected comparison columns
        """
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        PredefinedValidations._assert_columns_exist(source_df, key_columns, "source_data")
        PredefinedValidations._assert_columns_exist(target_df, key_columns, "target_data")

        if compare_columns is None:
            common_cols = [c for c in source_df.columns if c in target_df.columns]
            compare_columns = [c for c in common_cols if c not in key_columns]

        PredefinedValidations._assert_columns_exist(source_df, compare_columns, "source_data")
        PredefinedValidations._assert_columns_exist(target_df, compare_columns, "target_data")

        source_view = source_df[list(key_columns) + list(compare_columns)].copy()
        target_view = target_df[list(key_columns) + list(compare_columns)].copy()

        merge_df = source_view.merge(
            target_view,
            on=list(key_columns),
            how="outer",
            suffixes=("_source", "_target"),
            indicator=True,
        )

        missing_in_target = merge_df[merge_df["_merge"] == "left_only"][list(key_columns)]
        extra_in_target = merge_df[merge_df["_merge"] == "right_only"][list(key_columns)]

        both_df = merge_df[merge_df["_merge"] == "both"].copy()
        mismatch_records: List[Dict[str, Any]] = []

        for col in compare_columns:
            source_col = f"{col}_source"
            target_col = f"{col}_target"

            left = PredefinedValidations._normalize_series(both_df[source_col])
            right = PredefinedValidations._normalize_series(both_df[target_col])

            diff_mask = ~(left.eq(right) | (left.isna() & right.isna()))
            if diff_mask.any():
                diff_rows = both_df.loc[diff_mask, list(key_columns) + [source_col, target_col]].head(
                    max_mismatch_rows
                )
                mismatch_records.extend(diff_rows.to_dict(orient="records"))

        summary = {
            "missing_in_target_count": int(len(missing_in_target)),
            "extra_in_target_count": int(len(extra_in_target)),
            "mismatch_count": int(len(mismatch_records)),
            "sample_missing_in_target": missing_in_target.head(max_mismatch_rows).to_dict(orient="records"),
            "sample_extra_in_target": extra_in_target.head(max_mismatch_rows).to_dict(orient="records"),
            "sample_mismatches": mismatch_records[:max_mismatch_rows],
        }

        if (
            summary["missing_in_target_count"] > 0
            or summary["extra_in_target_count"] > 0
            or summary["mismatch_count"] > 0
        ):
            raise AssertionError(f"Record-level comparison failed: {summary}")

        return summary

    @staticmethod
    def incremental_delta_validation(
        source_data: DataLike,
        target_data: DataLike,
        watermark_column: str,
        key_columns: Sequence[str],
        delta_start: Optional[Union[str, pd.Timestamp]] = None,
        delta_end: Optional[Union[str, pd.Timestamp]] = None,
        allow_empty_delta: bool = True,
    ) -> Dict[str, Any]:
        """Validate that source delta records (by watermark) are present in target."""
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        required_cols = list(key_columns) + [watermark_column]
        PredefinedValidations._assert_columns_exist(source_df, required_cols, "source_data")
        PredefinedValidations._assert_columns_exist(target_df, required_cols, "target_data")

        source_df = source_df.copy()
        target_df = target_df.copy()

        source_df[watermark_column] = pd.to_datetime(source_df[watermark_column], errors="coerce")
        target_df[watermark_column] = pd.to_datetime(target_df[watermark_column], errors="coerce")

        if source_df[watermark_column].isna().any():
            raise AssertionError(
                f"Source contains invalid datetime values in watermark column '{watermark_column}'."
            )
        if target_df[watermark_column].isna().any():
            raise AssertionError(
                f"Target contains invalid datetime values in watermark column '{watermark_column}'."
            )

        start = pd.to_datetime(delta_start) if delta_start is not None else source_df[watermark_column].min()
        end = pd.to_datetime(delta_end) if delta_end is not None else source_df[watermark_column].max()

        source_delta = source_df[
            (source_df[watermark_column] >= start) & (source_df[watermark_column] <= end)
        ]
        target_delta = target_df[
            (target_df[watermark_column] >= start) & (target_df[watermark_column] <= end)
        ]

        if source_delta.empty and not allow_empty_delta:
            raise AssertionError(
                f"No source delta records found in range [{start}, {end}] for watermark '{watermark_column}'."
            )

        source_keys = set(map(tuple, source_delta[list(key_columns)].drop_duplicates().to_records(index=False)))
        target_keys = set(map(tuple, target_delta[list(key_columns)].drop_duplicates().to_records(index=False)))

        missing_keys = source_keys - target_keys
        extra_keys = target_keys - source_keys

        summary = {
            "delta_start": str(start),
            "delta_end": str(end),
            "source_delta_rows": int(len(source_delta)),
            "target_delta_rows": int(len(target_delta)),
            "missing_key_count": int(len(missing_keys)),
            "extra_key_count": int(len(extra_keys)),
            "sample_missing_keys": list(missing_keys)[:10],
            "sample_extra_keys": list(extra_keys)[:10],
        }

        if missing_keys:
            raise AssertionError(f"Incremental/delta validation failed: {summary}")

        return summary

    @staticmethod
    def referential_integrity_validation(
        child_data: DataLike,
        parent_data: DataLike,
        child_fk_columns: Sequence[str],
        parent_pk_columns: Sequence[str],
    ) -> int:
        """Validate that all child foreign keys exist in parent keys."""
        child_df = PredefinedValidations._to_dataframe(child_data, dataset_name="child_data")
        parent_df = PredefinedValidations._to_dataframe(parent_data, dataset_name="parent_data")

        if len(child_fk_columns) != len(parent_pk_columns):
            raise AssertionError(
                "child_fk_columns and parent_pk_columns must have the same number of columns."
            )

        PredefinedValidations._assert_columns_exist(child_df, child_fk_columns, "child_data")
        PredefinedValidations._assert_columns_exist(parent_df, parent_pk_columns, "parent_data")

        child_keys = child_df[list(child_fk_columns)].dropna().drop_duplicates()
        child_keys.columns = list(parent_pk_columns)
        parent_keys = parent_df[list(parent_pk_columns)].drop_duplicates()

        missing_fk = child_keys.merge(parent_keys, how="left", on=list(parent_pk_columns), indicator=True)
        missing_fk = missing_fk[missing_fk["_merge"] == "left_only"]

        missing_count = int(len(missing_fk))
        if missing_count > 0:
            raise AssertionError(
                "Referential integrity failed: "
                f"{missing_count} foreign key combinations in child not found in parent. "
                f"Sample: {missing_fk.head(10).to_dict(orient='records')}"
            )

        return missing_count

    @staticmethod
    def threshold_based_validation(
        source_value: Union[int, float],
        target_value: Union[int, float],
        allowed_percentage_diff: float,
        metric_name: str = "metric",
    ) -> float:
        """Validate two numeric values within an allowed percentage difference."""
        if allowed_percentage_diff < 0:
            raise AssertionError("allowed_percentage_diff must be >= 0.")

        source_num = float(source_value)
        target_num = float(target_value)

        if source_num == 0 and target_num == 0:
            return 0.0
        if source_num == 0 and target_num != 0:
            raise AssertionError(
                f"Threshold validation failed for {metric_name}: source is 0, target is {target_num}."
            )

        percentage_diff = abs(target_num - source_num) / abs(source_num) * 100
        if percentage_diff > allowed_percentage_diff:
            raise AssertionError(
                f"Threshold validation failed for {metric_name}: "
                f"source={source_num}, target={target_num}, diff={percentage_diff:.4f}%, "
                f"allowed={allowed_percentage_diff}%."
            )

        return percentage_diff

    @staticmethod
    def date_range_validation(
        data: DataLike,
        date_column: str,
        min_date: Optional[Union[str, pd.Timestamp]] = None,
        max_date: Optional[Union[str, pd.Timestamp]] = None,
        allow_nulls: bool = False,
    ) -> Tuple[pd.Timestamp, pd.Timestamp]:
        """Validate that date column values are inside configured date bounds."""
        df = PredefinedValidations._to_dataframe(data, dataset_name="data")
        PredefinedValidations._assert_columns_exist(df, [date_column], "data")

        dates = pd.to_datetime(df[date_column], errors="coerce")
        if not allow_nulls and dates.isna().any():
            raise AssertionError(
                f"Date range validation failed: invalid or NULL dates found in '{date_column}'."
            )

        non_null_dates = dates.dropna()
        if non_null_dates.empty:
            raise AssertionError(f"Date range validation failed: no valid dates in '{date_column}'.")

        observed_min = non_null_dates.min()
        observed_max = non_null_dates.max()

        if min_date is not None and observed_min < pd.to_datetime(min_date):
            raise AssertionError(
                f"Date range validation failed: minimum '{date_column}' is {observed_min}, "
                f"expected >= {pd.to_datetime(min_date)}."
            )

        if max_date is not None and observed_max > pd.to_datetime(max_date):
            raise AssertionError(
                f"Date range validation failed: maximum '{date_column}' is {observed_max}, "
                f"expected <= {pd.to_datetime(max_date)}."
            )

        return observed_min, observed_max

    @staticmethod
    def negative_value_validation(
        data: DataLike,
        columns: Sequence[str],
        allow_zero: bool = True,
    ) -> Dict[str, int]:
        """Validate that numeric columns do not contain negative values."""
        df = PredefinedValidations._to_dataframe(data, dataset_name="data")
        PredefinedValidations._assert_columns_exist(df, columns, "data")

        failures: Dict[str, int] = {}
        counts: Dict[str, int] = {}

        for col in columns:
            numeric_col = pd.to_numeric(df[col], errors="coerce")
            if numeric_col.isna().all() and not df[col].isna().all():
                raise AssertionError(
                    f"Negative value validation failed: column '{col}' contains non-numeric values."
                )

            mask = numeric_col < 0 if allow_zero else numeric_col <= 0
            count = int(mask.sum())
            counts[col] = count
            if count > 0:
                failures[col] = count

        if failures:
            rule_text = "< 0" if allow_zero else "<= 0"
            raise AssertionError(
                f"Negative value validation failed for rule {rule_text}: {failures}"
            )

        return counts

    @staticmethod
    def empty_dataset_validation(data: DataLike, dataset_name: str = "dataset") -> int:
        """Validate dataset is not empty."""
        df = PredefinedValidations._to_dataframe(data, dataset_name=dataset_name)
        row_count = len(df)
        if row_count == 0:
            raise AssertionError(f"{dataset_name} is empty; expected at least one row.")
        return row_count
    @staticmethod
    def group_by_distribution_validation(
        source_data: DataLike,
        target_data: DataLike,
        group_columns: Sequence[str],
        tolerance: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Validate grouped distribution between source and target datasets.

        Example:
            group_columns = ['isdelete']
            group_columns = ['status']
            group_columns = ['fiscalyear','company']

        tolerance:
            Allowed percentage difference per group.
        """
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        PredefinedValidations._assert_columns_exist(source_df, group_columns, "source_data")
        PredefinedValidations._assert_columns_exist(target_df, group_columns, "target_data")

        source_group = source_df.groupby(list(group_columns)).size().reset_index(name="source_count")
        target_group = target_df.groupby(list(group_columns)).size().reset_index(name="target_count")

        merged = source_group.merge(
            target_group,
            on=list(group_columns),
            how="outer"
        ).fillna(0)

        mismatches = []

        for _, row in merged.iterrows():
            source_count = float(row["source_count"])
            target_count = float(row["target_count"])

            if source_count == 0 and target_count == 0:
                continue

            if source_count == 0 and target_count != 0:
                mismatches.append(dict(row))
                continue

            percentage_diff = abs(target_count - source_count) / source_count * 100

            if percentage_diff > tolerance:
                mismatches.append(dict(row))

        if mismatches:
            raise AssertionError(
                f"Group distribution validation failed. Sample mismatches: {mismatches[:10]}"
            )

        return {
            "group_count": len(merged),
            "message": "Group distribution validation passed"
        }


    @staticmethod
    def custom_column_comparison(
        source_data: DataLike,
        target_data: DataLike,
        key_columns: Sequence[str],
        column_mapping: Mapping[str, str],
        source_transformers: Optional[Mapping[str, Callable[[pd.Series], pd.Series]]] = None,
        target_transformers: Optional[Mapping[str, Callable[[pd.Series], pd.Series]]] = None,
        max_mismatch_rows: int = 10,
    ) -> Dict[str, Any]:
        """Compare custom mapped columns between source and target on business keys.

        Parameters
        ----------
        column_mapping:
            Mapping of source column -> target column.
        source_transformers / target_transformers:
            Optional per-column transformers applied before comparison.
        """
        source_df = PredefinedValidations._to_dataframe(source_data, dataset_name="source_data")
        target_df = PredefinedValidations._to_dataframe(target_data, dataset_name="target_data")

        PredefinedValidations._assert_columns_exist(source_df, key_columns, "source_data")
        PredefinedValidations._assert_columns_exist(target_df, key_columns, "target_data")

        source_cols = list(column_mapping.keys())
        target_cols = list(column_mapping.values())

        PredefinedValidations._assert_columns_exist(source_df, source_cols, "source_data")
        PredefinedValidations._assert_columns_exist(target_df, target_cols, "target_data")

        source_transformers = dict(source_transformers or {})
        target_transformers = dict(target_transformers or {})

        source_view = source_df[list(key_columns) + source_cols].copy()
        target_view = target_df[list(key_columns) + target_cols].copy()

        for source_col, transformer in source_transformers.items():
            if source_col in source_view.columns:
                source_view[source_col] = transformer(source_view[source_col])

        for target_col, transformer in target_transformers.items():
            if target_col in target_view.columns:
                target_view[target_col] = transformer(target_view[target_col])

        merge_df = source_view.merge(
            target_view,
            on=list(key_columns),
            how="inner",
            suffixes=("_source", "_target"),
        )

        mismatches: List[Dict[str, Any]] = []

        for source_col, target_col in column_mapping.items():
            left = PredefinedValidations._normalize_series(merge_df[source_col])
            right = PredefinedValidations._normalize_series(merge_df[target_col])

            diff_mask = ~(left.eq(right) | (left.isna() & right.isna()))
            if diff_mask.any():
                diff_rows = merge_df.loc[
                    diff_mask, list(key_columns) + [source_col, target_col]
                ].head(max_mismatch_rows)
                mismatches.extend(diff_rows.to_dict(orient="records"))

        summary = {
            "joined_row_count": int(len(merge_df)),
            "mismatch_count": int(len(mismatches)),
            "sample_mismatches": mismatches[:max_mismatch_rows],
        }

        if summary["mismatch_count"] > 0:
            raise AssertionError(f"Custom column comparison failed: {summary}")

        return summary
