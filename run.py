import openai
import json
from dotenv import load_dotenv
import os

# Загрузка API-ключа из .env файла
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def chat_completion(prompt, model="gpt-4", temperature=0, response_format=None):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        # Извлечение токенов
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        print(f"Токены запроса: {prompt_tokens}")
        print(f"Токены ответа: {completion_tokens}")
        print(f"Общее количество токенов: {total_tokens}")

        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Ошибка при вызове OpenAI API: {e}")
        return None


def the_reviewer(prompt_initialization, current_prompt):
    prompt_reviewer = prompt_initialization + "\n\n"
    prompt_reviewer += f"Это мой промпт: {current_prompt}\n\n"
    prompt_reviewer += """Задание: Оцените мой промпт от 0 до 5 (0 — плохой, 5 — идеальный). Напишите, что можно улучшить, чтобы он стал идеальным (5)."""

    reviews = chat_completion(prompt_reviewer)
    print("Критика промпта:")
    print(reviews)

    return reviews


def the_questioner(prompt_initialization, current_prompt, reviews, questions_answers):
    prompt_questioner = prompt_initialization + "\n\n"
    prompt_questioner += f"Это мой промпт: {current_prompt}\n\n"
    prompt_questioner += f"Критический отзыв на промпт: {reviews}\n\n"
    prompt_questioner += """Задание: Составьте список из максимум 4 кратких вопросов, ответы на которые помогут улучшить промпт. 
    Ответ должен быть в формате JSON, который можно обработать с помощью json.loads.
    Пример: {"Questions": ["Вопрос 1", "Вопрос 2", "Вопрос 3", "Вопрос 4"]}"""

    questions_json = chat_completion(prompt_questioner, model="gpt-4", response_format={"type": "json_object"})

    try:
        questions = json.loads(questions_json).get('Questions', [])
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON с вопросами.")
        questions = []

    for i, question in enumerate(questions, start=1):
        answer = input(f"Вопрос {i}: {question} ")
        questions_answers += f"Вопрос: {question}\nОтвет: {answer}\n\n"

    return questions_answers


def the_prompt_maker(prompt_initialization, current_prompt, reviews, questions_answers):
    prompt = prompt_initialization + "\n\n"
    prompt += f"Это мой текущий промпт: {current_prompt}\n\n"
    prompt += f"Критический отзыв: {reviews}\n\n"
    prompt += f"Вопросы и ответы для улучшения: {questions_answers}\n\n"
    prompt += """Задание: Используя всю эту информацию, создайте новый идеальный промпт для GPT с оценкой 5. 
    В новом промпте укажите роли GPT, задайте контекст и четко сформулируйте задачу. 
    Выдайте только сам промпт, ничего лишнего."""

    new_prompt = chat_completion(prompt)
    return new_prompt


def promptor(initial_prompt, max_nb_iter=3):
    print(f"Ваш начальный промпт: {initial_prompt}")

    prompt_initialization = """Вы эксперт по написанию промптов для моделей больших языков. 
    Хороший промпт включает назначение роли GPT, четкий контекст, задание и ожидаемый формат ответа. 
    Вы мой личный помощник в создании промптов. Теперь я буду звать вас 'Promptor'."""

    current_prompt = initial_prompt
    questions_answers = ""
    for i in range(max_nb_iter):
        print(f"Итерация {i + 1}")
        reviews = the_reviewer(prompt_initialization, current_prompt)
        questions_answers = the_questioner(prompt_initialization, current_prompt, reviews, questions_answers)
        current_prompt = the_prompt_maker(prompt_initialization, current_prompt, reviews, questions_answers)

        print(f"\nНовый промпт: {current_prompt}\n\n")
        keep = input("Вы хотите сохранить этот промпт? (y/n): ")
        if keep.lower() == 'y':
            break

    return current_prompt


# Пример использования
prompt = promptor("Посоветуй мне главное блюдо на обед сегодня.", max_nb_iter=3)
res = chat_completion(prompt)
print("Результат:")
print(res)
