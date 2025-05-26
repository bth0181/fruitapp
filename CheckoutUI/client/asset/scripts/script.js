let InitialCount = -1;

const deleteProducts = async () => {
    const url = 'https://fruitapp-wwe3.onrender.com/product';

    try {
        const res = await axios.get(url);
        const products = res.data;

        for (const product of products) {
            await axios.delete(`${url}/${product.id}`);
        }

        location.reload();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
        console.error("Lỗi khi xóa sản phẩm:", error);
    }
};

const loadProducts = async () => {
    const url = 'https://fruitapp-wwe3.onrender.com/product';

    try {
        const res = await axios.get(url);
        const products = res.data;
        const len = products.length;

        if (len > InitialCount + 1) {
            $("#1").hide();
            $("#home").css("display", "grid");
            $("#2").css("display", "grid");

            let payable = 0;
            for (const product of products) {
                payable += parseFloat(product.payable);
            }

            const product = products.pop();
            const html = `
            <section>
                <div class="card card-long animated fadeInUp once">
                    <img src="asset/img/${product.id}.jpg" class="album">
                    <div class="span1">Product Name</div>
                    <div class="card__product"><span>${product.name}</span></div>
                    <div class="span2">Per Unit</div>
                    <div class="card__price"><span>${product.price}</span></div>
                    <div class="span3">Units</div>
                    <div class="card__unit"><span>${product.taken} ${product.units}</span></div>
                    <div class="span4">Payable</div>
                    <div class="card__amount"><span>${product.payable}</span></div>
                </div>
            </section>`;

            document.getElementById('home').innerHTML += html;
            document.getElementById('2').innerText = `CHECKOUT $${payable}`;
            InitialCount++;
        }
    } catch (error) {
        console.error("Lỗi khi load sản phẩm:", error);
    }
};

const checkout = async () => {
    document.getElementById('2').innerHTML = "<span class='loader-16' style='margin-left: 44%;'></span>";
    const url = 'https://fruitapp-wwe3.onrender.com/product';

    try {
        const res = await axios.get(url);
        const products = res.data;

        let payable = 0;
        for (const product of products) {
            payable += parseFloat(product.payable);
        }

        const qrText = `ĐƠN HÀNG 1 - TỔNG SỐ TIỀN CẦN THANH TOÁN: ${payable} VND`;
        const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qrText)}`;

        $("#home").hide();
        $("#final").hide();
        window.scrollTo({ top: 0, behavior: 'smooth' });

        $('#image').attr('src', qrUrl);
        $("#qr").css("display", "grid");

        setTimeout(() => {
            $("#qr").hide();
            $("#success").css("display", "grid");
            deleteProducts();
        }, 10000);
    } catch (error) {
        console.error("Lỗi khi tạo QR:", error);
    }
};
