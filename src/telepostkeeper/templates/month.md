# {{ header_title }}

[{{ header_description }}]({{ header_description_href }})

{% for post in posts %}

---

{% if post.photo %} 
![{{ post.photo }}]({{ post.photo }}) 
{% endif %}

### {{ post.title }}

{{ post.date }}

{% if post.forward %}

{{ post.forward.title }}

{{ post.forward.date }}

{% if post.text %}
{{ post.text | safe }}
{% endif %}

{% if post.path %}
🗂 File: [{{ post.path }}]({{ post.path }}) 
{% endif %}

{% else %}

{% if post.text %}

{{ post.text | safe }}

{% endif %}

{% if post.path %}
🗂 File: [{{ post.path }}]({{ post.path }}) 
{% endif %}

{% endif %}

{% endfor %}