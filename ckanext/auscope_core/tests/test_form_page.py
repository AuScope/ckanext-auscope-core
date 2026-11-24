"""Render the opt-in form components in CKAN's Jinja environment."""

from bs4 import BeautifulSoup
import pytest


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "auscope_core"),
    pytest.mark.usefixtures("with_plugins"),
]

IMPORT = """{% from 'snippets/auscope_core/form_page.html' import
    form_stages, form_header, form_navigation, form_actions with context %}"""


@pytest.fixture
def render(app):
    def render_components(markup, **context):
        with app.flask_app.test_request_context("/dataset/new"):
            template = app.flask_app.jinja_env.from_string(IMPORT + markup)
            return BeautifulSoup(template.render(**context), "html.parser")

    return render_components


def test_empty_components_add_no_markup(render):
    soup = render("""
        {{ form_stages([]) }}
        {{ form_actions() }}
        {% call form_navigation('Manage data') %} {% endcall %}
    """)
    assert not soup.find()


def test_single_stage_is_current_and_static(render):
    soup = render("{{ form_stages(stages) }}", stages=[
        {"label": "Research activity metadata", "state": "active"},
    ])
    progress = soup.select_one("ol[aria-label='Form progress']")
    assert len(progress.select("li")) == 1
    assert progress.select_one("span[aria-current=step]")
    marker = progress.select_one(".auscope-core-form-stage-marker")
    assert marker["aria-hidden"] == "true"
    assert not progress.select("a, button, [tabindex]")


def test_multiple_stages_preserve_order_and_native_controls(render):
    soup = render("{{ form_stages(stages, 'Deposit progress') }}", stages=[
        {"label": "Details", "state": "completed", "url": "/details"},
        {"label": "Files", "state": "active"},
        {"label": "Review", "submit": {"name": "save", "value": "go-review"}},
        {"label": "Finish", "state": "upcoming"},
    ])
    rows = soup.select("ol[aria-label='Deposit progress'] > li")
    assert [row["class"][-1] for row in rows] == [
        "auscope-core-form-stage--completed", "auscope-core-form-stage--active",
        "auscope-core-form-stage--upcoming", "auscope-core-form-stage--upcoming",
    ]
    assert rows[0].a["href"] == "/details"
    assert rows[0].select_one(".visually-hidden").get_text(strip=True) == "(Completed)"
    assert rows[1].select_one("[aria-current=step]")
    assert rows[2].select_one("button[type=submit][name=save][value=go-review]")
    assert rows[3].select_one(".visually-hidden").get_text(strip=True) == "(Upcoming)"
    assert not soup.select("[tabindex]")
    assert not rows[3].select("a, button")


def test_header_navigation_and_actions_accept_consumer_markup(render):
    soup = render("""
        {% set links %}
          {% call form_navigation('Manage data') %}
            <li><a href="/edit" aria-current="page">Details</a></li>
            <li><a href="/files">Files</a></li>
          {% endcall %}
        {% endset %}
        {% set view %}<a href="/data">View dataset</a>{% endset %}
        {{ form_header("Register <sample>", "Describe this sample.", view, links) }}
        <form>
          {% set previous %}
            <a class="btn btn-secondary" href="/details">Previous</a>
          {% endset %}
          {% set next %}<button class="btn btn-primary" name="save" value="next"
                               type="submit">Next</button>{% endset %}
          {% set notice %}<p class="action-info">Review the terms.</p>{% endset %}
          {{ form_actions(primary=next, secondary=previous, description=notice) }}
        </form>
    """)
    assert soup.h1.get_text(strip=True) == "Register <sample>"
    assert soup.select_one("header p").get_text(strip=True) == "Describe this sample."
    assert soup.select_one(".auscope-core-form-header-actions a")["href"] == "/data"
    assert soup.select_one("nav[aria-label='Manage data'] a[aria-current=page]")
    actions = soup.select_one("form .form-actions")
    notice = actions.select_one(".action-info")
    assert notice.get_text(strip=True) == "Review the terms."
    assert actions.select_one("a.btn-secondary")["href"] == "/details"
    assert actions.select_one("button.btn-primary[type=submit][name=save][value=next]")
    assert not soup.select("script, [tabindex]")


def test_header_and_primary_action_can_stand_alone(render):
    soup = render("""
        {{ form_header('Create record') }}
        {% set save %}<button type="submit">Save</button>{% endset %}
        {{ form_actions(primary=save) }}
    """)
    assert soup.select_one("header h1")
    assert not soup.select("header nav, header p, .auscope-core-form-header-actions")
    assert len(soup.select(".auscope-core-form-action-group")) == 1
