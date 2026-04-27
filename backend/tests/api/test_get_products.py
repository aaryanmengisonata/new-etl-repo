import requests

def test_get_products():
    response = requests.get(
        "https://fakestoreapi.com/products",
        verify=False
    )
    assert response.status_code == 200
