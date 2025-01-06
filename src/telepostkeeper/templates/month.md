# {{ header_title }}

[{{ header_description }}]({{ header_description_href }})

{% for post in posts %}

---

### {{ post.title }}

{% if post.photo %} 
![{{ post.photo }}]({{ post.photo }}) 
{% endif %}

{% if post.text %}
{{ post.text | safe }}
{% endif %}

{% if post.path %}
- 🗂 file: [{{ post.path }}]({{ post.path }}) 
{% endif %}

- date: {{ post.date }}

{% if post.forward %}
- forward title: {{ post.forward.title }}
- forward date: {{ post.forward.date }}
{% endif %}

{% endfor %}
