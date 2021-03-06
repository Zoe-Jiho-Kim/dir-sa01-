from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import certifi
from bson import ObjectId

ca = certifi.where()
client = MongoClient('---DB정보---',
                     tlsCAFile = ca)


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
# app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

# client = MongoClient('3.34.1.244', 27017, username="test", password="test")
db = client.dbsparta_plus_week4


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('index.html', user_info=user_info)
    except jwt.exceptions.DecodeError:
        return render_template('index.html')


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

# 로그인
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    # 로그인이 성공하면
    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        # 서버는 jwt토큰을 만들어서 클라이언트한테 발행 -> 클라이언트는 jwt토큰을 cookie에 저장했다가 유효할때까지 씀
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 회원가입
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

# 각 카테고리 클릭시 get요청, url에 카테고리 이름을 붙여서 keyword로 전달, 그 변수를 이용해 db에서 해당 카테고리를 찾습니다.
# url이 다르므로 모든 데이터를 항상 변수 items로 전달해도 변수가 겹칠 일이 없다고 생각했습니다.
@app.route("/<keyword>", methods=["GET"])
def item_get(keyword):
    all_item = list(db.devItems.find({"category": keyword}))
    token_receive = request.cookies.get('mytoken')
    if (token_receive == None):
        return render_template('index.html', items=all_item)
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})
    return render_template("index.html", items=all_item, user_info=user_info)

# 유저가 입력한 제품 데이터를 db에 저장
@app.route("/item", methods=["POST"])
def movie_post():
    url_receive = request.form['url_give']
    star_receive = request.form['star_give']
    comment_receive = request.form['comment_give']
    category_receive = request.form['category_give']
    username_receive = request.form['username_give']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_receive, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')
    title = soup.select_one('div.style_inner__1Eo2z > div.top_summary_title__15yAr > h2').text
    image = soup.select_one('div.style_content__36DCX > div > div.image_thumb_area__1dzNx > div > div > img')["src"]
    price = soup.select_one('div.lowestPrice_price_area__OkxBK > div.lowestPrice_low_price__fByaG > em').text
    spec = soup.select_one('head > meta:nth-child(12)')["content"]
    bs_01 = soup.select_one('div.bestReview_best_review__T0LD6 > ul > li:nth-child(1) > span').text
    bs_01_re = soup.select_one('div.bestReview_best_review__T0LD6 > ul > li:nth-child(1) > a > span').text
    bs_02 = soup.select_one('div.bestReview_best_review__T0LD6 > ul > li:nth-child(2) > span').text
    bs_02_re = soup.select_one('div.bestReview_best_review__T0LD6 > ul > li:nth-child(2) > a > span').text
    bs_03 = soup.select_one('div.bestReview_best_review__T0LD6 > ul > li:nth-child(3) > span').text
    bs_03_re = soup.select_one('div.bestReview_best_review__T0LD6 > ul > li:nth-child(3) > a > span').text

    doc = {
        "username": username_receive,
        "title": title,
        "image": image,
        "price": price,
        "spec": spec,
        "bs_01": bs_01,
        "bs_01_re": bs_01_re,
        "bs_02": bs_02,
        "bs_02_re": bs_02_re,
        "bs_03": bs_03,
        "bs_03_re": bs_03_re,
        "star": star_receive,
        "comment": comment_receive,
        "category": category_receive

    }
    db.devItems.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})

@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        comment_receive = request.form["comment_give"]
        target_item_id_receive = request.form["targetitemid_give"]
        db.devItems.update_one({'_id': ObjectId(target_item_id_receive)}, { '$addToSet': { "innercomment": {"owner":user_info["username"], "content":comment_receive}}})

        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('login.html', user_info=user_info)

@app.route('/item/comment', methods=['POST'])
def com_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 포스팅하기
        user_info = db.users.find_one({"username": payload["id"]})
        com_receive = request.form["com_give"]
        date_receive = request.form["date_give"]

        doc = {
            "username": user_info["username"],
            "comment": com_receive,
            "date": date_receive,
        }
        db.posts.insert_one(doc)
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return

@app.route("/get_posts", methods=['GET'])
def get_posts():
    posts = list(db.posts.find({}, {'_id': False}).sort("date", -1))
    print(posts)
    return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts": posts})

@app.route('/delete', methods=['POST'])
def delete_item():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})

    delete_item_id_receive = request.form['delete_item_id_give']
    print(delete_item_id_receive)
    thisitem = db.devItems.find_one({'_id': ObjectId(delete_item_id_receive)})

    if user_info["username"] == thisitem["username"]:
        db.devItems.delete_one({'_id': ObjectId(delete_item_id_receive)})
        return jsonify({'msg':'삭제 완료!'})
    else:
        return jsonify({"result": "본인이 업로드한 게시물만 삭제할 수 있습니다.", 'msg': '게시자만 삭제할 수 있습니다.'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
