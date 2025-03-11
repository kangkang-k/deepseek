import json
import sys
from datetime import datetime
from colorama import Fore, init
import requests
from openai import OpenAI
import textwrap



init(autoreset=True)

current_key = None
SESSION_FILE = "session.json"
API_FILE = "apikey.json"
try:
    with open(API_FILE, "r", encoding="utf-8") as f:
        api_key = json.load(f)
        current_key = api_key['key']
except:
    print(Fore.RED + "暂未未设置API_KEY，将无法使用会话，请执行相关指令进行设置")

try:
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        all_sessions = json.load(f)
except FileNotFoundError:
    all_sessions = {}

session_id = next(iter(all_sessions)) if all_sessions else None
current_session = session_id
models_li = {"R1": "deepseek-reasoner", "V3": "deepseek-chat"}
current_model = models_li['R1']


class NullWriter:
    def write(self, msg):
        pass


def beautify_code_output(code):
    border = '+' + '-' * (len(max(code.splitlines(), key=len)) + 2) + '+'
    print(Fore.GREEN + border)
    for line in code.splitlines():
        print(Fore.GREEN + f"| {line} |")
    print(Fore.GREEN + border)


def beautify_message(role, message):
    if role == "user":
        print(f"{Fore.GREEN}User: {Fore.WHITE}{message}")
    elif role == "assistant":
        print(f"{Fore.BLUE}Assistant: {Fore.WHITE}{message}")


def list_sessions():
    if all_sessions:
        print(Fore.YELLOW + "所有历史会话：")
        for session_id in all_sessions:
            print(Fore.CYAN + session_id)
    else:
        print(Fore.RED + "没有历史会话。")


def get_balance(currency="CNY"):
    url = "https://api.deepseek.com/user/balance"
    if current_key is None:
        print(Fore.RED + "请先设置API_KEY，否则无法获取余额")
        return None
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {current_key}'
    }

    response = requests.get(url, headers=headers)

    data = response.json()

    for balance_info in data['balance_infos']:
        if balance_info['currency'] == currency:
            return balance_info['total_balance']


def list_models():
    models = ["deepseek-reasoner(R1)", "deepseek-chat(V3)"]
    print(Fore.YELLOW + "可切换的模型列表：")
    for model in models:
        print(Fore.CYAN + model)


def create_session(session_id, musk):
    if session_id in all_sessions:
        print(Fore.RED + f"会话 '{session_id}' 已存在，无法创建。")
        return

    session_data = {
        "session_id": session_id,
        "messages": []
    }

    if musk is None:
        musk = "You are a helpful assistant."

    session_data['messages'].append({"role": "system", "content": musk})

    all_sessions[session_id] = session_data

    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(all_sessions, f, ensure_ascii=False, indent=4)

    original_stdout = sys.stdout
    sys.stdout = NullWriter()

    use_session(session_id)

    sys.stdout = original_stdout

    print(Fore.GREEN + f"已创建且切换到会话: {session_id}")


def remove_session(session_id):
    global current_session
    if session_id in all_sessions:
        del all_sessions[session_id]
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(all_sessions, f, ensure_ascii=False, indent=4)
        print(Fore.GREEN + f"删除会话: {session_id},并自动切换到第一个历史会话")
        session_id = next(iter(all_sessions)) if all_sessions else None
        current_session = session_id
    else:
        print(Fore.RED + f"不存在会话:{session_id}")


def show_current_session():
    global current_session
    if current_session is None:
        print(Fore.RED + "当前不在任何会话中，请先创建会话或加载会话")
        return
    print(Fore.YELLOW + f"当前会话:{Fore.CYAN}{current_session}")


def load_sessions():
    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(Fore.RED + "会话文件未找到！")
        return {}


def use_session(session_id):
    global current_session
    sessions = load_sessions()
    if session_id in sessions:
        current_session = session_id
        print(Fore.GREEN + f"已切换至会话：{Fore.CYAN}{session_id}")
    else:
        print(Fore.RED + f"会话 {Fore.YELLOW}{session_id}{Fore.RED} 不存在！")


def chmodel(model_id):
    global current_model
    current_model = models_li[model_id]
    print(Fore.GREEN + f"已切换至模型：{Fore.CYAN}{current_model}")


def chkey(key):
    global current_key
    if key == None:
        print(Fore.RED + "请在指令后拼接API_KEY")
        return
    current_key = key
    print(key)
    with open(API_FILE, "w", encoding="utf-8") as f:
        json.dump({"key": current_key}, f, ensure_ascii=False, indent=4)
    print(Fore.GREEN + f"已设置API_KEY为：{Fore.CYAN}{current_key}")


def start_chat(session_id=None):
    global current_key
    if current_key is None:
        print(Fore.RED + "请先设置API_KEY，否则无法使用会话")
        return
    client = OpenAI(api_key=current_key, base_url="https://api.deepseek.com")
    models_reflex = {
        "deepseek-reasoner": "R1",
        "deepseek-chat": "V3"
    }
    global current_session, current_model
    print(f"进入会话模式，当前模型：{models_reflex[current_model]} \n输入 'exit' 退出会话模式。")

    if session_id:
        if session_id in all_sessions:
            print(f"打开会话 {session_id}")
            session_data = all_sessions[session_id]
            messages_his = session_data["messages"]
            for message in messages_his:
                beautify_message(message['role'], message['content'])
        else:
            print(Fore.RED + f"会话 {session_id} 不存在")
            return
    else:
        if all_sessions:
            session_id = current_session
            print(f"继续第一个会话 {session_id}")
            session_data = all_sessions[session_id]
            messages_his = session_data["messages"]
            for message in messages_his:
                beautify_message(message['role'], message['content'])
            print()
        else:
            session_id = datetime.now().strftime("%Y%m%d%H%M%S")
            print(f"创建新的会话 {session_id}")
            session_data = {"session_id": session_id, "messages": []}
            session_data['messages'].append({"role": "system", "content": "禁止推理过程，回答尽量精细有质量"})
            all_sessions[session_id] = session_data

    while True:
        user_input = input(f"{Fore.GREEN}Question: {Fore.GREEN}")
        if user_input.lower() == 'exit':
            print(Fore.YELLOW + "退出会话模式，返回命令行界面。")
            break

        session_data["messages"].append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=current_model,
            messages=session_data["messages"],
            stream=True
        )
        content = ''
        print(
            f"{Fore.LIGHTBLUE_EX}Answer:{Fore.LIGHTWHITE_EX} 当前服务器响应较慢, 请耐心等待...(切换到V3模型也许会更快一点)\n",
            end='', flush=True)
        for chunk in response:
            if chunk.choices[0].delta.content:
                new_content = chunk.choices[0].delta.content
                content += new_content
                print(f"{Fore.LIGHTBLUE_EX}{new_content}", end='', flush=True)
        print('\n')
        session_data["messages"].append({"role": "assistant", "content": content})

        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(all_sessions, f, ensure_ascii=False, indent=4)


def main():
    def print_help():
        commands = [
            ("chkey <apikey>", "初始化或修改apikey"),
            ("list", "显示所有历史会话"),
            ("models", "显示可切换的模型列表"),
            ("mk <session_id> <musk>",
             "创建会话（mk hello将会创建一个id为hello的会话），musk参数可选，作用是提前告诉AI接下来应该处理什么内容，比如“你是一个python攻城狮，对代码及其精通”"),
            ("rm <session_id>", "删除会话（rm hello将会删除id为hello的会话）"),
            ("loc", "显示当前所在会话"),
            ("use <session_id>", "使用某个会话（use hello将会将当前会话切换到hello）"),
            ("start <session_id>",
             "开始聊天，进入专注模式（只输入start，则进入当前会话窗口，输入start hello将进入指定id的会话窗口）"),
            ("chmodel <model_id>", "切换模型（chmodel R1则切换到R1，chmodel V3则切换到V3，当前会话记忆不受影响）"),
            ("balance", "查询API余额"),
            ("help", "查看用法及示例"),
            ("exit", "退出程序")
        ]
        print(
            Fore.YELLOW + f"                         命令选项:                                                               power by kangkang")
        print(Fore.RED + "=" * 150)
        for command, description in commands:
            wrapped_desc = textwrap.fill(description, width=120, initial_indent="", subsequent_indent="")
            print(Fore.CYAN + f"{command.ljust(25)} {wrapped_desc}")
        print(Fore.RED + "=" * 150)

    print_help()
    while True:
        user_input = input(Fore.YELLOW + "输入指令 >>> ").strip()

        if user_input == 'exit':
            print(Fore.YELLOW + "退出已退出...")
            break

        elif user_input == 'list':
            list_sessions()

        elif user_input == 'models':
            list_models()

        elif user_input.startswith('mk'):
            try:
                session_id = user_input.split(' ')[1]
                musk = user_input.split(' ')[2] if len(user_input.split(' ')) > 2 else None
                create_session(session_id, musk)
            except:
                print(Fore.RED + "请在命令后拼接要新建的会话ID")

        elif user_input.startswith('rm'):
            try:
                session_id = user_input.split(' ')[1]
                remove_session(session_id)
            except:
                print(Fore.RED + "请在命令后拼接要删除的会话ID")

        elif user_input == 'loc':
            show_current_session()

        elif user_input.startswith('use'):
            try:
                session_id = user_input.split(' ')[1]
                use_session(session_id)
            except:
                print(Fore.RED + "请在命令后拼接要使用的会话ID")
        elif user_input == 'balance':
            balance = get_balance()
            if balance is not None:
                print(Fore.YELLOW + f"当前余额: {Fore.CYAN}{balance}")
        elif user_input.startswith('chkey'):
            new_key = user_input.split(' ')[1] if len(user_input.split()) > 1 else None
            chkey(new_key)

        elif user_input.startswith('start'):
            session_id = user_input.split(' ')[1] if len(user_input.split()) > 1 else None
            start_chat(session_id)

        elif user_input.startswith('chmodel'):
            try:
                model_id = user_input.split(' ')[1]
                chmodel(model_id)
            except:
                print(Fore.RED + "请在命令后拼接要切换的模型ID")

        elif user_input == 'help':
            print_help()
        else:
            print(Fore.RED + "未识别的命令，请输入有效的命令。")


if __name__ == "__main__":
    main()
