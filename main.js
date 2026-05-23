function searchProduct() {
    let query = document.getElementById("search").value;

    fetch(`/search?q=${query}`)
        .then(res => res.json())
        .then(data => {
            let tbody = document.querySelector("#productTable tbody");
            tbody.innerHTML = "";

            data.forEach(p => {
                tbody.innerHTML += `
                    <tr>
                        <td>${p.product_id}</td>
                        <td>${p.product_name}</td>
                        <td>${p.unit}</td>
                        <td>${p.Available_Quantity}</td>
                        <td class="${p.stock}">${p.stock}</td>
                        <td class="${p.price}">${p.price}</td>
                    </tr>
                `;
            });
        });
}

function filterVendor(value) {
    value = value.toLowerCase();
    let rows = document.querySelectorAll("#vendorTable tbody tr");

    rows.forEach(row => {
        let name = row.children[1].innerText.toLowerCase();
        row.style.display = name.includes(value) ? "" : "none";
    });
}