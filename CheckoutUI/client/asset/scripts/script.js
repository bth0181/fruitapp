var InitialCount = -1;

const deleteProducts = async () => {
    const url = 'https://fruitapp-wwe3.onrender.com/product';

    let res = await axios.get(url);
    const products = res.data;

    for (let product of products) {
        await axios.delete(`https://fruitapp-wwe3.onrender.com/product/${product.id}`);
    }

    location.reload();
    window.scroll({
        top: 0,
        left: 0,
        behavior: 'smooth'
    });
};

const loadProducts = async () => {
    const url = 'https://fruitapp-wwe3.onrender.com/product';

    let res = await axios.get(url);
    const products = res.data;
    var len = products.length;

    if (len > InitialCount + 1) {
        $("#1").css("display", "none");
        $("#home").css("display", "grid");
        $("#2").css("display", "grid");

        var payable = 0;
        var totalWeight = 0;

        for (let product of products) {
            payable += parseFloat(product.payable);
            totalWeight += parseFloat(product.total_weight || 0);  // Tính tổng khối lượng
        }

        var product = products.pop();
        const x = `
        <section>
            <div class="card card-long animated fadeInUp once">
                <img src="asset/img/${product.id}.jpg" class="album">
                <div class="span1">Product Name</div>
                <div class="card__product">
                    <span>${product.name}</span>
                </div>
                <div class="span2">Per Unit</div>
                <div class="card__price">
                    <span>${product.price}</span>
                </div>
                <div class="span3">Units</div>
                <div class="card__unit">
                    <span>${product.taken} ${product.units}</span>
                </div>
                <div class="span4">Payable</div>
                <div class="card__amount">
                    <span>${product.payable}</span>
                </div>
            </div>
        </section>
        `;

        // Render sản phẩm
        document.getElementById('home').innerHTML += x;

        // Cập nhật checkout và khối lượng tổng
        document.getElementById('2').innerHTML = `
            CHECKOUT $${payable}
            <div style="margin-top: 10px; font-weight: bold; color: #555; font-size: 14px;">
                TỔNG KHỐI LƯỢNG: ${totalWeight} g
            </div>
        `;

        InitialCount += 1;
    }
};

const checkout = async () => {
    document.getElementById('2').innerHTML = "<span class='loader-16' style='margin-left: 44%;'></span>";
    const url = 'https://fruitapp-wwe3.onrender.com/product';

    let res = await axios.get(url);
    const products = res.data;

    let payable = 0;
    for (let product of products) {
        payable += parseFloat(product.payable);
    }

    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=ĐƠN HÀNG 1 - TỔNG SỐ TIỀN CẦN THANH TOÁN: ${payable} VND`;

    $("#home").css("display", "none");
    $("#final").css("display", "none");
    window.scroll({ top: 0, left: 0, behavior: 'smooth' });

    $('#image').attr('src', qrUrl);
    $("#qr").css("display", "grid");

    setTimeout(() => {
        $("#qr").css("display", "none");
        $("#success").css("display", "grid");
        deleteProducts();
    }, 10000);
};
