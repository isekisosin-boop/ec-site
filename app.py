from flask import Flask, render_template, request, redirect, url_for, session
import os
import resend
from dotenv import load_dotenv
load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
from datetime import datetime

app = Flask(__name__, static_folder="static", static_url_path="/static")

# セッションを利用するための秘密鍵
app.secret_key = "ec-site-development-key"


# =========================
# 商品データ
# =========================

products_data = {
    1: {
        "name": "crystaljoy",
        "category": "口腔ケア",
        "description": "あのオラが昔愛用していた伝説の歯磨き粉",
        "price": "¥2,000",
        "detail": "昔オラが使用していました",
        "features": "オラの歯はピカピカです。お母ちゃんにも褒められました",
        "usage": "使用方法がここに入ります。使用する量や使用するタイミングなどを掲載します。",
        "notes": "注意事項がここに入ります。使用上の注意や保管方法などを掲載します。",
        "image": "images/商品1.jpg"
    },

    2: {
        "name": "安眠膝",
        "category": "スキンケア",
        "description": "あの暴れん坊オラもぐっすり寝てしまいます",
        "price": "¥100,000",
        "detail": "ただのひょっとこのひざです",
        "features": "商品の特徴がここに入ります。商品の魅力やポイントを掲載します。",
        "usage": "使用方法がここに入ります。使用する量や使用するタイミングなどを掲載します。",
        "notes": "注意事項がここに入ります。使用上の注意や保管方法などを掲載します。",
        "image": "images/商品2.jpg"
    },

    3: {
        "name": "レア写真",
        "category": "シャンプー",
        "description": "みたことないような表情を激写したレア写真です",
        "price": "¥1,000,000,000",
        "detail": "ただのオラの写真でした",
        "features": "商品の特徴がここに入ります。商品の魅力やポイントを掲載します。",
        "usage": "使用方法がここに入ります。使用する量や使用するタイミングなどを掲載します。",
        "notes": "注意事項がここに入ります。使用上の注意や保管方法などを掲載します。",
        "image": "images/商品3.jpg"
    }
}


# =========================
# カテゴリー対応
# =========================

category_map = {
    "oral": "口腔ケア",
    "skin": "スキンケア",
    "shampoo": "シャンプー",
    "other": "その他"
}


# =========================
# ホーム
# =========================

@app.route("/")
def index():
    return render_template(
        "index.html",
        products=products_data
    )


# =========================
# 商品一覧
# =========================

@app.route("/products")
def products():

    category = request.args.get("category")
    search_query = request.args.get("q", "").strip()
    sort_order = request.args.get("sort", "default")

    filtered_products = products_data

    # -------------------------
    # カテゴリー絞り込み
    # -------------------------

    if category:
        category_name = category_map.get(category)

        if category_name:
            filtered_products = {
                product_id: product
                for product_id, product in filtered_products.items()
                if product["category"] == category_name
            }

    # -------------------------
    # 商品検索
    # -------------------------

    if search_query:
        search_text = search_query.lower()

        filtered_products = {
            product_id: product
            for product_id, product in filtered_products.items()
            if search_text in product["name"].lower()
            or search_text in product["category"].lower()
            or search_text in product["description"].lower()
            or search_text in product["detail"].lower()
        }

    # -------------------------
    # 並び順
    # -------------------------

    if sort_order == "name":
        filtered_products = dict(
            sorted(
                filtered_products.items(),
                key=lambda item: item[1]["name"]
            )
        )

    return render_template(
        "products.html",
        products=filtered_products,
        selected_category=category,
        search_query=search_query,
        sort_order=sort_order
    )


# =========================
# 商品詳細
# =========================

@app.route("/products/<int:product_id>")
def product_detail(product_id):

    product = products_data.get(product_id)

    if product is None:
        return "商品が見つかりません", 404

    return render_template(
        "product_detail.html",
        product=product,
        product_id=product_id
    )


# =========================
# カートに追加
# =========================

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):

    product = products_data.get(product_id)

    if product is None:
        return "商品が見つかりません", 404

    quantity = request.form.get("quantity", 1, type=int)

    if quantity < 1:
        quantity = 1

    cart = session.get("cart", {})

    product_key = str(product_id)

    if product_key in cart:
        cart[product_key] += quantity
    else:
        cart[product_key] = quantity

    session["cart"] = cart

    return redirect(url_for("cart"))


# =========================
# カート数量変更
# =========================

@app.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart(product_id):

    if product_id not in products_data:
        return "商品が見つかりません", 404

    quantity = request.form.get("quantity", 1, type=int)

    cart = session.get("cart", {})
    product_key = str(product_id)

    if quantity <= 0:
        cart.pop(product_key, None)
    else:
        cart[product_key] = quantity

    session["cart"] = cart

    return redirect(url_for("cart"))


# =========================
# カートから商品削除
# =========================

@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):

    cart = session.get("cart", {})
    product_key = str(product_id)

    cart.pop(product_key, None)

    session["cart"] = cart

    return redirect(url_for("cart"))


# =========================
# カート
# =========================

@app.route("/cart")
def cart():

    cart_data = session.get("cart", {})

    cart_items = []
    total_quantity = 0

    for product_id, quantity in cart_data.items():

        product = products_data.get(int(product_id))

        if product is None:
            continue

        cart_items.append({
            "id": int(product_id),
            "product": product,
            "quantity": quantity
        })

        total_quantity += quantity

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_quantity=total_quantity
    )


# =========================
# 購入手続き
# =========================

@app.route("/checkout")
def checkout():

    cart_data = session.get("cart", {})

    if not cart_data:
        return redirect(url_for("cart"))

    return render_template(
        "checkout.html"
    )


# =========================
# 注文内容確認
# =========================

@app.route("/checkout/confirm", methods=["POST"])
def checkout_confirm():

    cart_data = session.get("cart", {})

    if not cart_data:
        return redirect(url_for("cart"))

    customer = {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "postal_code": request.form.get("postal_code", "").strip(),
        "address": request.form.get("address", "").strip(),
        "phone": request.form.get("phone", "").strip()
    }

    # 入力内容をセッションに一時保存
    session["customer"] = customer

    cart_items = []
    total_quantity = 0

    for product_id, quantity in cart_data.items():

        product = products_data.get(int(product_id))

        if product is None:
            continue

        cart_items.append({
            "id": int(product_id),
            "product": product,
            "quantity": quantity
        })

        total_quantity += quantity

    return render_template(
        "checkout_confirm.html",
        customer=customer,
        cart_items=cart_items,
        total_quantity=total_quantity
    )


# =========================
# 注文確定
# =========================

@app.route("/order/complete", methods=["POST"])
def order_complete():

    cart_data = session.get("cart", {})
    customer = session.get("customer")

    # カートまたはお客様情報がない場合
    if not cart_data or not customer:
        return redirect(url_for("cart"))

    cart_items = []
    total_quantity = 0

    for product_id, quantity in cart_data.items():

        product = products_data.get(int(product_id))

        if product is None:
            continue

        cart_items.append({
            "id": int(product_id),
            "product": product,
            "quantity": quantity
        })

        total_quantity += quantity

    # 仮の注文番号を作成
    order_number = datetime.now().strftime("EC%Y%m%d%H%M%S")

    # 注文完了ページで使用する情報を一時保存
    session["completed_order"] = {
        "order_number": order_number,
        "customer": customer,
        "cart_items": [
            {
                "id": item["id"],
                "quantity": item["quantity"]
            }
            for item in cart_items
        ],
        "total_quantity": total_quantity
    }

    # 注文確定後はカートを空にする
    session.pop("cart", None)
    session.pop("customer", None)

    return redirect(url_for("order_complete_page"))


# =========================
# 注文完了ページ
# =========================

@app.route("/order/complete")
def order_complete_page():

    completed_order = session.get("completed_order")

    if not completed_order:
        return redirect(url_for("products"))

    cart_items = []

    for item in completed_order["cart_items"]:

        product = products_data.get(item["id"])

        if product is None:
            continue

        cart_items.append({
            "id": item["id"],
            "product": product,
            "quantity": item["quantity"]
        })

    return render_template(
        "order_complete.html",
        order_number=completed_order["order_number"],
        customer=completed_order["customer"],
        cart_items=cart_items,
        total_quantity=completed_order["total_quantity"]
    )


# =========================
# ブランドについて
# =========================

@app.route("/about")
def about():
    return render_template("about.html")


# =========================
# よくある質問
# =========================

@app.route("/faq")
def faq():
    return render_template("faq.html")

# =========================
# お問い合わせ
# =========================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        category = request.form.get("category", "").strip()
        message = request.form.get("message", "").strip()

        # 必須項目チェック
        if not name or not email or not category or not message:
            return render_template(
                "contact.html",
                error="必須項目を入力してください。",
                form_data=request.form
            )

        # -------------------------
        # メール送信
        # -------------------------

        email_body = f"""
        <h2>お問い合わせがありました</h2>

        <p><strong>お名前：</strong>{name}</p>

        <p><strong>メールアドレス：</strong>{email}</p>

        <p><strong>電話番号：</strong>{phone or "未入力"}</p>

        <p><strong>お問い合わせ項目：</strong>{category}</p>

        <p><strong>お問い合わせ内容：</strong></p>

        <p>{message.replace(chr(10), "<br>")}</p>
        """

        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": ["isekisosin@gmail.com"],
            "subject": f"【EC SITE】お問い合わせ：{category}",
            "html": email_body,
        })

        return render_template(
            "contact_complete.html",
            name=name,
            email=email,
            category=category,
            message=message
        )

    return render_template("contact.html")
# =========================
# ログイン
# =========================

@app.route("/login")
def login():
    return render_template("login.html")


# =========================
# アプリ起動
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=5001)