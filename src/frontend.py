import asyncio
import calendar
import os
import pathlib
import pprint
from datetime import datetime

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from utils import read_yaml

load_dotenv()


ENV_NAME_STORE = 'TELEPOSTKEEPER_STORE_DIR'

store = os.getenv(ENV_NAME_STORE)
if not store or store == ".":
    store = pathlib.Path(".")
else:
    store = pathlib.Path(store.strip())
store.mkdir(parents=True, exist_ok=True)
print('🏈️ store: ', store)


async def make_index_chat_month(month: pathlib.Path, about: dict):
    print('💚 Month: ', month)
    print()

    posts = sorted(list(filter(lambda file: file.is_file() and file.suffix == '.yaml', month.iterdir())), reverse=True)
    posts_cnt = []
    for post in posts:
        print('POST')
        posts_cnt.append({'title':f'Post {post.stem}'})

    month_full_name = datetime.strptime(month.name, "%m").strftime("%B")
    title = f'{month_full_name} {month.parent.name}'
    description = month.parent.parent.name

    template = Environment(loader=FileSystemLoader("templates")).get_template("month.html")
    html_data = template.render({
        'title': title,
        'description': description,
        'posts': posts_cnt})

    with month.joinpath('index.html').open('w') as f:
        f.write(html_data)


async def make_index_chat(chat: pathlib.Path, about: dict):
    print('💙 Chat: ', chat)

    years = sorted(list(filter(lambda file: file.is_dir() and file.name.isdigit(), chat.iterdir())), reverse=True)
    years_context = []
    for year in years:
        months = sorted(list(filter(lambda file: file.is_dir() and file.name.isdigit(), year.iterdir())), reverse=True)
        months_context = []
        for month in months:
            month_full_name = datetime.strptime(month.name, "%m").strftime("%B")
            months_context.append({
                'title': month_full_name,
                'folder': month,
            })

            await make_index_chat_month(month, about)

        years_context.append({
            'title': year.name,
            'months': months_context})

    template = Environment(loader=FileSystemLoader("templates")).get_template("chat.html")
    html_data = template.render({'title': f'{chat.name}', 'years': years_context})

    with chat.joinpath('index.html').open('w') as f:
        f.write(html_data)


async def make_index_store():
    chats = sorted(list(filter(lambda file: file.is_dir() and file.name.startswith('chat-'), store.iterdir())), reverse=True)

    chats_all_context = []
    for chat in chats:
        about_path = chat / 'about.yaml'
        about = await read_yaml(about_path)

        attributes = ['id', 'title', 'full_name', 'username', 'last_name', 'first_name']
        context = dict()

        for attr in attributes:
            if attr in about:
                if value := about[attr]:
                    context[attr] = value

        context['folder'] = chat.name

        if 'encryption' in about:
            title = f'{chat.name} (🔐 encrypted)'
            context['title'] = title

        await make_index_chat(chat, context)

        chats_all_context.append(context)

    template = Environment(loader=FileSystemLoader("templates")).get_template("store.html")
    html_data = template.render({'title': f'Index of chats', 'chats': chats_all_context})

    with store.joinpath('index.html').open('w') as f:
        f.write(html_data)





def main():
    print('🏞 Frontend: ')

    print('🏞 Store Index: ')
    asyncio.run(make_index_store())

    print('🏞 end.')


if __name__ == '__main__':
    main()






