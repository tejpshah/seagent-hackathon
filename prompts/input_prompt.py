from jinja2 import Template
from data_accessor.data_dao import get_all_columns
# Define a list of column names (Example: fetched from a DataFrame)
columns = get_all_columns()

# Jinja2 template
template_string = """
The dataset contains the following columns:

{% for column in columns %}
- {{ column }}
{% endfor %}

Please provide values for each column to complete the data entry.
"""

# Create and render template
template = Template(template_string)
output = template.render(columns=columns)

print(output)
