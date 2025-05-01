from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.post("/")
def calculate_score():
    """
    POSTリクエストで {"sentences": [...], "counts": [...]} を受け取り、
    {"scores": [...]} を返すエンドポイント。
    """
    # 1. リクエストがJSON形式かチェック
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    # 2. リクエストボディからJSONデータを取得
    data = request.get_json()

    # 3. 必要なキーが存在するかチェック
    if 'sentences' not in data or 'counts' not in data:
        return jsonify({"error": "Missing 'sentences' or 'counts' in request body"}), 400

    sentences = data['sentences']
    counts = data['counts']

    # 4. 入力データの型と長さを簡易チェック (任意)
    if not isinstance(sentences, list) or not isinstance(counts, list):
         return jsonify({"error": "'sentences' and 'counts' must be lists"}), 400
    if len(sentences) != len(counts):
         return jsonify({"error": "'sentences' and 'counts' lists must have the same length"}), 400

    # counts の要素が数値であることを確認しながら計算
    scores = []
    for count in counts:
        if not isinstance(count, (int, float)):
            return jsonify({"error": f"Element in 'counts' is not a number: {count}"}), 400

        scores.append(count + 3) # ここで実際の処理を行う

    # 6. 結果をJSON形式でレスポンスとして返す
    response_data = {"scores": scores}
    return jsonify(response_data), 200 # 成功を示すステータスコード 200 を返す

# スクリプトが直接実行された場合に開発用サーバーを起動
if __name__ == '__main__':
    # host='0.0.0.0' を指定すると、ローカルネットワーク内の他のデバイスからもアクセス可能になります。
    # debug=True は開発時に便利ですが、本番環境ではFalseにしてください。
    app.run(port=12500)
