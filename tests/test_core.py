from app.core import emails_from_html, school_name, contact_links, greeting, parse_search_results

def test_extracts_visible_and_mailto_only():
    html='<h1>Escola Demo</h1><a href="mailto:secretaria@escola.pt">Contacto</a><p>direcao@escola.pt</p><script>hidden@escola.pt</script>'
    assert emails_from_html(html)==['direcao@escola.pt','secretaria@escola.pt']
    assert school_name(html,'escola.pt')=='Escola Demo'

def test_contact_links_same_host():
    html='<a href="/contactos">Contactos</a><a href="https://outsider.pt/">Outro</a>'
    assert contact_links(html,'https://escola.pt/', 'escola.pt')==['https://escola.pt/contactos']

def test_greeting():
    assert 'Escola A' in greeting('Escola A')

def test_search_results():
    assert parse_search_results('<li class="b_algo"><h2><a href="https://escola.pt">Escola</a></h2></li>') == ['https://escola.pt']
