from google import genai

def main():
    # 默认会从环境变量 GEMINI_API_KEY 读取
    client = genai.Client(api_key="AIzaSyC2y_FKbvA4CV4Au2jh62i16zvjhv9XPsI")

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="用一句话解释什么是机器学习。"
    )

    print(resp.text)

if __name__ == "__main__":
    main()
