/*
 * Copyright (c) Microsoft Corporation. All rights reserved. Licensed under the MIT license.
 * See LICENSE in the project root for license information.
 */

/* global document, Office, Word */

Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    // Gắn sự kiện click cho nút "Gửi câu hỏi"
    // Đảm bảo nút này tồn tại trong taskpane.html
    document.getElementById("ask-button").onclick = sendQuestion;
  }
});

async function sendQuestion() {
  const questionInput = document.getElementById("question");
  const answerBox = document.getElementById("answer-box");

  const query = questionInput.value;
  if (!query) {
    answerBox.innerText = "Lỗi: Bạn chưa nhập câu hỏi.";
    return;
  }

  // Hiển thị trạng thái chờ
  answerBox.innerHTML = '<span style="color: #666; font-style: italic;">Đang xử lý...</span>';

  try {
    // Bước 1: Lấy toàn bộ văn bản từ file Word
    answerBox.innerText = "Đang lấy nội dung từ Word...";
    const documentText = await getDocumentText();
    
    answerBox.innerText = "Đã lấy văn bản. Đang gửi đến Bot...";

    // Bước 2: Gọi API Flask (Backend) của bạn
    const answer = await callChatbotAPI(documentText, query);

    // Bước 3: Hiển thị kết quả
    answerBox.innerText = answer;

  } catch (error) {
    answerBox.innerText = "Đã xảy ra lỗi: " + error.message;
    console.error(error);
  }
}

/**
 * Lấy toàn bộ nội dung text từ body của tài liệu Word.
 */
function getDocumentText() {
  return new Promise((resolve, reject) => {
    Word.run(async (context) => {
      try {
        const body = context.document.body;
        body.load("text"); // Yêu cầu tải thuộc tính 'text'
        await context.sync();
        resolve(body.text);
      } catch (error) {
        reject(error);
      }
    });
  });
}

/**
 * Gọi API Flask (chạy trên localhost:5000)
 */
async function callChatbotAPI(context, query) {
  // Link đến Flask Backend (Bước 1)
  // Đây là lý do chúng ta cần khai báo 'http://localhost:5000' trong manifest.xml
  const apiUrl = "http://localhost:5000/qa"; 

  const response = await fetch(apiUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      context: context,
      query: query
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`Lỗi API (${response.status}): ${errorData.error || response.statusText}`);
  }

  const data = await response.json();
  return data.answer; // Lấy kết quả từ { "answer": "..." }
}