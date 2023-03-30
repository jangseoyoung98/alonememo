# 크래프톤 정글 2기 장서영
from random import *
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://seoyoung:seoyoung@15.164.245.163', 27017)
db = client.dbjungle

# (메모를 하나씩 생성할 때마다, mongoDB에 별도의 card_id를 부여하기 위해 전역변수를 선언)  
nextId = -1 
id_list = []

## index.html 렌더링
@app.route('/')
def home():
    return render_template('index.html')


## 1. 리스팅 API - 저장된 카드 보여주기 (Read)
@app.route('/memo/list', methods=['GET'])
def read_memos():
    # 1) mongoDB에서 _id 값을 제외한 모든 데이터를 조회해서, 'like'가 많은 순으로 정렬된 리스트를 memos 변수에 담는다. (내림차순)
    memos = list(db.memos.find({}, {'_id': False}).sort('like', -1))
    
    # 화면을 띄울 때, 메모 카드들을 불러옴과 동시에 id_list를 셋팅한다.
    # 새로고침 하더라도 id_list에 card_id들이 중복되어 들어가지 않도록 한다.
    global id_list
    temp = list(db.memos.find({}, {'_id': False, 'title': False, 'text': False, 'like': False}))
    for one in temp:
        card_id = one['card_id']
        if card_id not in id_list:
            id_list.append(card_id)

    # 2) 성공하면, success 메시지와 함께 memos라는 키 값으로 memos 정보를 반환다.
    return jsonify({'result': 'success', 'memos': memos})


## 2. 저장 API - 카드 생성 (Create)
@app.route('/memo/post', methods=['POST'])
def post_memo():
    # 1) 클라이언트로부터 데이터를 받는다.
    title_receive = request.form['title_give']  # memo-title을 받는 부분
    text_receive = request.form['text_give']    # memo-content를 받는 부분

    # 2) mongoDB에 데이터를 넣는다. (도큐먼트를 생성할 때마다, 고유의 id 값을 부여한다.)
    global nextId
    global id_list
    while True:
        nextId = randint(1, 1024)
        if nextId in id_list:
            continue
        else :
            id_list.append(nextId)
            break

    memo = {'title': title_receive, 'text': text_receive, 'like': 0, 'card_id': nextId}
    db.memos.insert_one(memo)

    # 3) 성공하면 success 메시지를 반환한다.
    return jsonify({'result':'success'})


## 3. 수정 API - 카드 수정 (Update)
@app.route('/memo/update', methods=['POST'])
def modify_memo():
    # 1) 클라이언트로부터 데이터를 받는다.
    title_receive = request.form['title_give'] # new-title을 받는 부분 
    text_receive = request.form['text_give']   # new-text를 받는 부분
    id_receive = int(request.form['id_give'])  # 해당 카드(메모)의 고유 id를 받는 부분 (int 형변환 필요)
    
    # 2) mongoDB에 데이터를 업데이트 한다. (받은 new-title과 new-text로 변경) 
    db.memos.update_one({'card_id': id_receive}, {"$set": {"title": title_receive, "text": text_receive}})

    # 3) 성공하면 success 메시지를 반환한다.
    return jsonify({'result': 'success'})
    

## 4. 삭제 API - 카드 삭제 (Delete)
@app.route('/memo/delete', methods=['POST'])
def delete_memo():
    # 1) 클라이언트로부터 데이터를 받는다.
    id_receive = int(request.form["id_give"])  # 해당 카드(메모)의 고유 id를 받는 부분 (int 형변환 필요)

    # 2) mongoDB 내 memos에서 card_id가 id_receive와 일치하는 memo(도큐먼트)를 찾아 제거한다. 
    # 추가로 id_list에서 해당 card_id도 제거한다.
    global id_list
    memo = db.memos.find_one({"card_id": id_receive})
    delete_id = int(memo['card_id'])
    id_list.remove(delete_id)

    db.memos.delete_one({"card_id": id_receive})

    # 3) 성공하면 success 메시지를 반환한다.
    return jsonify({'result': 'success'})


## 5. 좋아요 API - 카드 좋아요 수 1 증가 (Update)
@app.route('/memo/like', methods=['POST'])
def like_memo():
    # 1) 클라이언트로부터 데이터를 받는다.
    id_receive = int(request.form['id_give'])  # 해당 카드(메모)의 고유 id를 받는 부분 (int 형변환 필요)

    # 2) mongoDB 내 memos에서 card_id가 id_receive와 일치하는 memo(도큐먼트)를 찾아낸다.
    # 해당 memo의 원래 like 갯수를 like_bf 변수에 담아서, 1 증가시킨 후 like_af 변수에 할당한다.
    memo = db.memos.find_one({'card_id': id_receive})
    like_bf = int(memo['like'])
    like_af = like_bf + 1

    # 3) mongoDB에 데이터를 업데이트 한다. (해당 memo의 like를 like_af로 변경) 
    db.memos.update_one({'card_id': id_receive}, {"$set": {'like': like_af}})

    # 4) 성공하면 success 메시지를 반환한다.
    return jsonify({'result': 'success'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)