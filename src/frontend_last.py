#!/usr/bin/env python
import re
from string import Template

import telegram
import yaml
from jinja2 import Environment, FileSystemLoader
from urlextract import URLExtract

import config
from utils import read_file, write_file


def text_Preprocessing(text_html):
    text_html = str(text_html)
    #print('🦜', 'Preprocessing text: ')
    #print(text_html)
    #print('==============')

    if urls := URLExtract().find_urls(text_html):
        for url in urls:
            text_html = text_html.replace(url, f'<a href="{url}">{url}</a>')

    text_html = text_html.replace('\n', '<br>\n')

    return text_html





def renderForwardPostContent(message: telegram.Message, data: dict):
    print('🛍 Forward')
    print('Message: ')
    print(message)
    print('===========')
    print()
    print()

    contents = []

    forw_chat = ''
    if hasattr(message, 'forward_from_chat'):
        if hasattr(message.forward_from_chat, 'title'):
            forw_chat += f'<strong>{message.forward_from_chat.title}</strong>'

        if hasattr(message.forward_from_chat, 'username'):
            forw_chat += f'<small>({message.forward_from_chat.username})</small>'

        if hasattr(message.forward_from_chat, 'id'):
            forw_chat += f' <small>[{message.forward_from_chat.id}]</small>'

    contents.append(f'<h5>{forw_chat}</h5>')

    if hasattr(message, 'forward_date'):
        contents.append(f'<p>{message.forward_date}</p>')

    contents.append(f'TEXT')
    contents.append('==========')
    contents.append(text_Preprocessing(data.get('text_html')))

    content = '<br>'.join(contents)

    forw_templ = '''
    <div class="border border-primary ml-2 pl-3" 
        style="
            border-right: none!important;
            margin-left: .5rem;
            padding-left: 1rem;
            border-bottom: none!important;
            border-top: none!important;
            border-width: 1px!important;">
            $content
            </div>
            '''

    content = Template(forw_templ).substitute(content=content)

    return content

    template = Environment(loader=FileSystemLoader("templates")).get_template("forwardPostContent.html")
    return template.render(
        {'title': f'Post {message.message_id}',
         'date': message.date.__str__(),
         'content': content,
         })


def makeIndexOneChat(chat):
    print('🧿 makeIndexOneChat(): ', chat.name)

    chat_about = chat.joinpath('about.yml')
    chat_about_text = read_file(chat_about)
    chat_about_yml = yaml.load(chat_about_text, Loader=yaml.Loader)
    chat_title = chat_about_yml.get('title')
    chat_title_small = chat_about_yml.get('title_small')
    chat_id = chat_about_yml.get('id')
    index_title = f'{chat_title} (chat: {chat_id})'

    posts = sorted(list(filter(lambda file: file.name.startswith('post-') and file.name.endswith('.yml'), chat.iterdir())), reverse=True)

    posts_context = []
    for post in posts:
        print('📮 Post: ', post.name)

        text_post = read_file(post)
        yaml_post = yaml.load(text_post, Loader=yaml.Loader)

        message_post = yaml_post.get('message')
        data_post = yaml_post.get('data')

        post_context = dict()

        post_context['title'] = f'Post {message_post.message_id}'
        post_context['date'] = message_post.date.__str__()

        text_html = data_post.get('text_html')
        if text_html == None:
            text_html = ''

        if hasattr(message_post, 'forward_date') and message_post.forward_date:
            post_context['text'] = renderForwardPostContent(message_post, data_post)
        else:
            post_context['text'] = text_Preprocessing(text_html)

        if data_post.get('photo'):
            post_context['photo'] = data_post.get('photo')

        posts_context.append(post_context)

    template = Environment(loader=FileSystemLoader("templates")).get_template("index-chat-posts.html")
    write_file(chat.joinpath('index.html'), template.render({
        'title': f'{chat_title_small} | Index',
        'posts': posts_context,
        'chat': {
            'title': chat_title,
            'title_small': chat_title_small,
            'id': chat_id
        }
    }))

    print('🚢️ Make: chat/index.txt ')
    posts_index_txt = '\n'.join(reversed([post.relative_to(chat).as_posix() for post in posts]))
    write_file(chat.joinpath('index.txt'), posts_index_txt)


def makeIndexAllChats():
    print('💎️ makeIndexAllChats(): ')

    if not config.CHATS_STORE.exists():
        print('🚫 not config.CHATS_STORE.exists()')
        return

    chat_dirs = sorted(list(filter(lambda file: file.is_dir() and file.name.startswith('chat-'), config.CHATS_STORE.iterdir())), reverse=True)
    for chat in chat_dirs:
        makeIndexOneChat(chat)

    print()
    print('💎️ make All Index (): ')
    chats_context = []
    for chat in chat_dirs:
        chat_about = chat.joinpath('about.yml')
        chat_about_text = read_file(chat_about)
        chat_about_yml = yaml.load(chat_about_text, Loader=yaml.Loader)
        chat_title = chat_about_yml.get('title')
        chat_title_small = chat_about_yml.get('title_small')
        chat_id = chat_about_yml.get('id')

        chats_context.append({
            'href': chat.name,
            'title': chat_title,
            'title_small': chat_title_small,
            'id': chat_id,
        })

    template = Environment(loader=FileSystemLoader("templates")).get_template("index-store-chats.html")
    write_file(config.CHATS_STORE.joinpath('index.html'), template.render({
        'title': f'Index of the Store',
        'chats': chats_context}))

    print('🏰 Make: store/index.txt ')
    chats_index_txt = '\n'.join(reversed([chat.relative_to(config.CHATS_STORE).as_posix() for chat in chat_dirs]))
    write_file(config.CHATS_STORE.joinpath('index.txt'), chats_index_txt)


if __name__ == '__main__':
    makeIndexAllChats()