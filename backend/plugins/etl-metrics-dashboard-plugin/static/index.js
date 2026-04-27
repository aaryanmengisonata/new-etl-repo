'use strict';

(function () {
    var DASHBOARD_ATTACHMENT_NAME = 'ETL Metrics Dashboard Data';
    var DASHBOARD_ATTACHMENT_SOURCE = 'etl-metrics-dashboard-attachment.json';

    allure.api.addTranslation('en', {
        tab: {
            etlMetricsDashboard: {
                name: 'ETL Metrics Dashboard'
            }
        }
    });

    function flattenLeafTests(node, output) {
        if (!node) {
            return;
        }
        if (node.children && node.children.length) {
            node.children.forEach(function (child) {
                flattenLeafTests(child, output);
            });
            return;
        }
        if (node.uid) {
            output.push(node.uid);
        }
    }

    function findLabel(labels, name) {
        if (!labels || !labels.length) {
            return null;
        }
        var match = labels.find(function (label) {
            return label.name === name;
        });
        return match ? match.value : null;
    }

    function normalizeLabelValue(value, fallback) {
        var cleaned = (value === null || value === undefined || String(value).trim() === '') ? fallback : String(value).trim();
        return cleaned;
    }

    function collectAttachments(testCase) {
        var attachments = [];

        function crawlStep(step) {
            if (!step) {
                return;
            }
            if (step.attachments && step.attachments.length) {
                step.attachments.forEach(function (attachment) {
                    attachments.push(attachment);
                });
            }
            if (step.steps && step.steps.length) {
                step.steps.forEach(crawlStep);
            }
        }

        if (testCase && testCase.testStage) {
            if (testCase.testStage.attachments && testCase.testStage.attachments.length) {
                testCase.testStage.attachments.forEach(function (attachment) {
                    attachments.push(attachment);
                });
            }
            if (testCase.testStage.steps && testCase.testStage.steps.length) {
                testCase.testStage.steps.forEach(crawlStep);
            }
        }

        return attachments;
    }

    function findDashboardAttachmentSource(testCases) {
        for (var i = 0; i < testCases.length; i += 1) {
            var attachments = collectAttachments(testCases[i]);
            for (var j = 0; j < attachments.length; j += 1) {
                var attachment = attachments[j] || {};
                if (attachment.name === DASHBOARD_ATTACHMENT_NAME || attachment.source === DASHBOARD_ATTACHMENT_SOURCE) {
                    return attachment.source;
                }
            }
        }
        return null;
    }

    function buildPayloadFromLabels(testCases) {
        var records = testCases.map(function (testCase, index) {
            var sourceValue = Number(findLabel(testCase.labels, 'Source_Count'));
            var targetValue = Number(findLabel(testCase.labels, 'Target_Count'));

            if (Number.isNaN(sourceValue) || Number.isNaN(targetValue)) {
                return null;
            }

            var tableName = normalizeLabelValue(findLabel(testCase.labels, 'Table'), 'N/A');
            var validationType = normalizeLabelValue(findLabel(testCase.labels, 'Validation'), 'N/A');
            var testName = normalizeLabelValue(testCase.name, '');
            var testCaseMatch = String(testName).match(/(TEST[_-]?\d+)/i);
            var testCaseId = testCaseMatch ? String(testCaseMatch[1]).toUpperCase().replace('-', '_') : ('TEST_' + String(index + 1).padStart(2, '0'));

            return {
                testCase: testCaseId,
                testName: testName,
                status: normalizeLabelValue(testCase.status, 'unknown'),
                source: {
                    label: 'Bronze (Source)',
                    table: tableName,
                    lakehouse: normalizeLabelValue(findLabel(testCase.labels, 'Source_Lakehouse'), 'N/A'),
                    validation: validationType,
                    value: sourceValue
                },
                target: {
                    label: 'Silver (Target)',
                    table: tableName,
                    lakehouse: normalizeLabelValue(findLabel(testCase.labels, 'Target_Lakehouse'), 'N/A'),
                    validation: validationType,
                    value: targetValue
                }
            };
        }).filter(function (item) {
            return item !== null;
        });

        return {
            title: 'Bronze vs Silver Data Validation Checks',
            xAxisTitle: 'Test Cases',
            yAxisTitle: 'Number of Lines (Count)',
            records: records
        };
    }

    function buildChartConfig(payload) {
        var records = payload.records || [];
        records = records.map(function (record, index) {
            var normalized = record || {};
            if (!normalized.testCase) {
                normalized.testCase = 'TEST_' + String(index + 1).padStart(2, '0');
            }
            if (!normalized.status) {
                normalized.status = 'unknown';
            }
            return normalized;
        });
        var labels = records.map(function (record) { return record.testCase; });
        var sourceValues = records.map(function (record) { return Number(record.source.value) || 0; });
        var targetValues = records.map(function (record) { return Number(record.target.value) || 0; });
        var statuses = records.map(function (record) {
            return normalizeLabelValue(record.status, 'unknown').toLowerCase();
        });
        var isFailedIndex = function (index) {
            var status = statuses[index] || 'unknown';
            return status === 'failed' || status === 'broken' || status === 'error';
        };

        return {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Bronze (Source)',
                        data: sourceValues,
                        backgroundColor: function (ctx) {
                            var area = ctx.chart.chartArea;
                            if (!area) {
                                return '#b07a45';
                            }
                            var gradient = ctx.chart.ctx.createLinearGradient(area.left, 0, area.right, 0);
                            gradient.addColorStop(0, '#8b5a2b');
                            gradient.addColorStop(0.5, '#d9a46f');
                            gradient.addColorStop(1, '#8b5a2b');
                            return gradient;
                        },
                        borderWidth: function (ctx) {
                            return isFailedIndex(ctx.dataIndex) ? 3 : 1.5;
                        },
                        borderColor: function (ctx) {
                            return isFailedIndex(ctx.dataIndex) ? '#c62828' : '#724721';
                        },
                        borderSkipped: false,
                        borderRadius: 2,
                        categoryPercentage: 0.75,
                        barPercentage: 0.85
                    },
                    {
                        label: 'Silver (Target)',
                        data: targetValues,
                        backgroundColor: function (ctx) {
                            var area = ctx.chart.chartArea;
                            if (!area) {
                                return '#a3a3a3';
                            }
                            var gradient = ctx.chart.ctx.createLinearGradient(area.left, 0, area.right, 0);
                            gradient.addColorStop(0, '#7f7f7f');
                            gradient.addColorStop(0.5, '#cfcfcf');
                            gradient.addColorStop(1, '#7f7f7f');
                            return gradient;
                        },
                        borderWidth: function (ctx) {
                            return isFailedIndex(ctx.dataIndex) ? 3 : 1.5;
                        },
                        borderColor: function (ctx) {
                            return isFailedIndex(ctx.dataIndex) ? '#c62828' : '#696969';
                        },
                        borderSkipped: false,
                        borderRadius: 2,
                        categoryPercentage: 0.75,
                        barPercentage: 0.85
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            boxWidth: 14,
                            color: '#2a2f35',
                            font: {
                                size: 13
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: payload.title || 'Bronze vs Silver Data Validation Checks',
                        color: '#1e2328',
                        font: {
                            size: 22,
                            weight: '500'
                        },
                        padding: {
                            top: 8,
                            bottom: 18
                        }
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function (context) {
                                var pair = records[context.dataIndex] || {};
                                var point = context.datasetIndex === 0 ? pair.source : pair.target;
                                if (!point) {
                                    return '';
                                }
                                var details = [
                                    'Status: ' + String((records[context.dataIndex] || {}).status || 'unknown').toUpperCase(),
                                    'Table: ' + normalizeLabelValue(point.table, 'N/A'),
                                    'Lakehouse: ' + normalizeLabelValue(point.lakehouse, 'N/A'),
                                    'Validation: ' + normalizeLabelValue(point.validation, 'N/A')
                                ];
                                var optionalName = normalizeLabelValue((records[context.dataIndex] || {}).testName, '');
                                if (optionalName) {
                                    details.unshift('Name: ' + optionalName);
                                }
                                return details;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: payload.yAxisTitle || 'Number of Lines (Count)',
                            color: '#2a2f35',
                            font: {
                                size: 15,
                                weight: '600'
                            }
                        },
                        ticks: {
                            color: '#2a2f35'
                        },
                        grid: {
                            color: '#d5dbe2'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: payload.xAxisTitle || 'Test Cases',
                            color: '#2a2f35',
                            font: {
                                size: 15,
                                weight: '600'
                            }
                        },
                        ticks: {
                            color: '#2a2f35',
                            font: {
                                size: 14
                            }
                        },
                        grid: {
                            color: '#eceff3'
                        }
                    }
                },
                layout: {
                    padding: {
                        left: 12,
                        right: 12,
                        top: 4,
                        bottom: 0
                    }
                }
            }
        };
    }

    var DashboardView = Backbone.Marionette.View.extend({
        className: 'etl-metrics-dashboard',

        template: function () {
            return (
                '<div class="etl-metrics-dashboard__card">' +
                '<div class="etl-metrics-dashboard__canvas-wrap">' +
                '<canvas id="etl-metrics-dashboard-canvas"></canvas>' +
                '</div>' +
                '<div class="etl-metrics-dashboard__message">Loading ETL metrics...</div>' +
                '</div>'
            );
        },

        onRender: function () {
            var view = this;
            var messageNode = view.$('.etl-metrics-dashboard__message');
            var canvasNode = view.$('#etl-metrics-dashboard-canvas')[0];

            jQuery.getJSON('data/suites.json').then(function (suitesData) {
                var uids = [];
                flattenLeafTests(suitesData, uids);

                var requests = uids.map(function (uid) {
                    return jQuery.getJSON('data/test-cases/' + uid + '.json').then(
                        function (testCaseData) { return testCaseData; },
                        function () { return null; }
                    );
                });

                Promise.all(requests).then(function (testCases) {
                    var loadedCases = testCases.filter(function (item) { return item !== null; });
                    var dashboardAttachmentSource = findDashboardAttachmentSource(loadedCases);

                    var payloadPromise = dashboardAttachmentSource
                        ? jQuery.getJSON('data/attachments/' + dashboardAttachmentSource)
                        : Promise.resolve(buildPayloadFromLabels(loadedCases));

                    payloadPromise.then(function (payload) {
                        if (!payload || !payload.records || !payload.records.length) {
                            messageNode.text('No ETL metrics found. Attach "ETL Metrics Dashboard Data" JSON or add Source_Count/Target_Count labels.');
                            return;
                        }

                        messageNode.hide();
                        var config = buildChartConfig(payload);
                        new Chart(canvasNode.getContext('2d'), config);
                    }, function () {
                        messageNode.text('Unable to load ETL metrics dashboard JSON attachment from report data.');
                    });
                });
            }, function () {
                messageNode.text('Unable to load suites data from report.');
            });
        }
    });

    allure.api.addTab('etl-metrics-dashboard', {
        title: 'tab.etlMetricsDashboard.name',
        icon: 'fa fa-bar-chart',
        route: 'etl-metrics-dashboard',
        onEnter: function () {
            return new DashboardView();
        }
    });
})();
