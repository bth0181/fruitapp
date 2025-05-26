var InitialCount = -1;

const deleteProducts = async () => {
    const url = 'https://fruitapp-wwe3.onrender.com/product';

    let res = await axios.get(url);
    const products = res.data;

    for (let product of products) {
        await axios.delete(`${url}/${product.id}`);
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
    const len = products.length;

    if (len > InitialCount + 1) {
        $("#1").css("display", "none");
        $("#home").css("display", "grid");
        $("#2").css("display", "grid");

        let payable = 0;
        let totalWeight = 0;

        for (let product of products) {
            payable += parseFloat(product.payable);
            totalWeight += parseFloat(product.total_weight || 0);
        }

        const product = products.pop();
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
                    <span>${product.taken}</span> <!-- Không hiển thị chữ units -->
                </div>
                <div class="span4">Payable</div>
                <div class="card__amount">
                    <span>${product.payable}</span>
                </div>
            </div>
        </section>
        `;

        document.getElementById('home').innerHTML += x;

        // Giao diện TỔNG KHỐI LƯỢNG trong ô
        document.getElementById('2').innerHTML = `
            <div class="card__amount" style="margin-bottom: 10px; font-size: 14px;">
                TỔNG KHỐI LƯỢNG: ${totalWeight} G
            </div>
            <button class="checkout" onclick="checkout()">CHECKOUT $${payable}</button>
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
