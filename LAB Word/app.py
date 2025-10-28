from flask import Flask, request, jsonify
from flask_cors import CORS # Quan trọng: Để cho phép Javascript (ở Bước 2) gọi

# Khởi tạo Flask
app = Flask(__name__)
# Cho phép gọi API từ bất kỳ đâu (cần thiết cho localhost)
CORS(app) 

# Đây là nơi bạn sẽ tích hợp LangChain
def get_answer_from_langchain(context, query):
    # ----- BẮT ĐẦU PHẦN GIẢ LẬP -----
    #
    # Tạm thời, chúng ta chỉ giả lập là nó hoạt động
    # để bạn test giao diện.
    # Khi chạy thật, bạn thay thế phần này bằng code
    # LangChain Q&A (với vector store, chain.run()...) của bạn
    #
    print(f"Đã nhận Context: {len(context)} ký tự")
    print(f"Đã nhận Query: {query}")
    
    if "xin chào" in query.lower():
        return "Chào bạn, tôi là bot Q&A!"
    
    # Giả lập tìm kiếm
    if "Hà Nội" in context and "thủ đô" in query:
        return "Dựa trên văn bản, Hà Nội là thủ đô của Việt Nam."
        
    return f"Bot đã nhận câu hỏi: '{query}'. (Đây là câu trả lời demo)"
    # ----- KẾT THÚC PHẦN GIẢ LẬP -----


# Tạo một API route tên là /qa
@app.route("/qa", methods=["POST"])
def process_qa():
    try:
        data = request.json
        
        # Lấy văn bản từ Word (context)
        context = data.get("context") 
        # Lấy câu hỏi từ người dùng (query)
        query = data.get("query")

        if not context or not query:
            return jsonify({"error": "Thiếu 'context' hoặc 'query'"}), 400

        # Gọi "bộ não" LangChain của bạn
        answer = get_answer_from_langchain(context, query)

        # Trả kết quả về cho Word Add-in
        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Chạy server Backend này
if __name__ == "__main__":
    # Chạy trên cổng 5000
    app.run(port=5000, debug=True)