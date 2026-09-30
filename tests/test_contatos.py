import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from discovery.cli import main
from discovery.collectors.filiais import build_cnpj
from discovery.contatos import (
    COLUMNS, ContatosError, build_rows, cnae_id, cnae_text, export, find_latest_run,
    format_natureza, format_phone, format_state, load_ajustes, mask_cnpj, render_csv,
)

MODELO = Path(__file__).parent.parent / "contatoexemplo" / "Contato (res.partner).csv"
ROOT = "11222333"
MATRIZ = build_cnpj(ROOT, 1)
FILIAL = build_cnpj(ROOT, 2)


def cadastro(**extra):
    base = {
        "razao_social": "ACME TECNOLOGIA LTDA", "descricao_tipo_de_logradouro": "RUA",
        "logradouro": "JAVARI", "numero": "234", "cep": "93534180", "municipio": "NOVO HAMBURGO",
        "uf": "RS", "ddd_telefone_1": "5199363972", "email": "COMERCIAL@ACME.COM.BR",
        "codigo_natureza_juridica": 2062, "natureza_juridica": "Sociedade Empresária Limitada",
        "capital_social": 80000, "opcao_pelo_simples": True, "opcao_pelo_mei": False,
        "cnae_fiscal": 2731700, "cnae_fiscal_descricao": "Fabricação de aparelhos",
        "cnaes_secundarios": [{"codigo": 3321000, "descricao": "Instalação de máquinas"},
                              {"codigo": 4321500, "descricao": "Instalação elétrica"},
                              {"codigo": 4742300, "descricao": "Comércio de material elétrico"}],
    }
    return {**base, **extra}


def raw(filiais=True, cnpj_status="ok"):
    fontes = [{"tipo": "cnpj", "status": cnpj_status, "erro": "falhou" if cnpj_status != "ok" else None,
               "conteudo": {"cnpj": MATRIZ, "dados": {**cadastro(), "identificador_matriz_filial": 1}}
               if cnpj_status == "ok" else None}]
    if filiais:
        fontes.append({"tipo": "filiais", "status": "ok", "conteudo": {"raiz": ROOT, "estabelecimentos": [
            {"cnpj": MATRIZ, "tipo": "matriz", "cadastro": cadastro()},
            {"cnpj": FILIAL, "tipo": "filial",
             "cadastro": cadastro(logradouro="OUTRA", cnaes_secundarios=[], municipio="SAO PAULO", uf="SP")},
        ]}})
    return {"cliente": {"id": "acme", "nome": "Acme", "site": "https://acme.com.br"}, "fontes": fontes}


def parse(rows):
    return list(csv.reader(render_csv(rows).splitlines()))


@pytest.mark.skipif(not MODELO.exists(), reason="CSV-modelo local (dados reais, fora do git)")
def test_header_matches_odoo_model_export():
    with MODELO.open(encoding="utf-8", newline="") as f:
        assert next(csv.reader(f)) == COLUMNS


def test_extra_rows_for_secondary_cnaes():
    rows = build_rows(raw(filiais=False)).rows
    assert len(rows) == 3  # 1 linha principal + 2 extras
    main, extra1, extra2 = rows
    sec_id = COLUMNS.index("CNAE Secundário/ID")
    assert main[sec_id] == "l10n_br_fiscal.cnae_3321000"
    assert extra1[sec_id] == "l10n_br_fiscal.cnae_4321500"
    assert extra2[sec_id] == "l10n_br_fiscal.cnae_4742300"
    for extra in (extra1, extra2):
        filled = [c for c, v in zip(COLUMNS, extra) if v]
        assert filled == ["CNAE Secundário", "CNAE Secundário/ID", "CNAE Secundário/Nome"]


def test_no_secondary_cnae_gives_only_main_row():
    rows = build_rows(raw(filiais=False) | {"fontes": [
        {"tipo": "cnpj", "status": "ok", "conteudo": {"cnpj": MATRIZ, "dados": cadastro(cnaes_secundarios=[])}}]}).rows
    assert len(rows) == 1 and rows[0][COLUMNS.index("CNAE Secundário")] == ""


def test_one_contact_per_establishment_with_mask():
    result = build_rows(raw())
    assert result.contatos == 2
    col = COLUMNS.index("ID do Imposto")
    ids = [r[col] for r in result.rows if r[col]]
    assert ids == [mask_cnpj(MATRIZ), mask_cnpj(FILIAL)] == ["11.222.333/0001-81", "11.222.333/0002-62"]
    end = COLUMNS.index("Endereço")
    assert [r[end] for r in result.rows if r[col]] == ["Rua Javari, 234", "Rua Outra, 234"]


def test_normalizations():
    main = build_rows(raw(filiais=False)).rows[0]
    value = dict(zip(COLUMNS, main))
    assert value["Razão Social"] == "Acme Tecnologia Ltda"
    assert value["Estado"] == "Rio Grande do Sul (BR)" and value["CEP"] == "93534-180"
    assert value["Telefone"] == "(51) 9936-3972" and not value["Telefone"].startswith("'")
    assert value["E-mail"] == "comercial@acme.com.br"
    assert value["Natureza Jurídica"] == "206-2 - Sociedade Empresária Limitada"
    assert value["Perfil Fiscal do Parceiro"] == "Contribuinte Simples Nacional"
    assert value["Capital Social"] == "80000.0"
    assert value["Site"] == "https://acme.com.br"
    assert (value["Idioma"], value["País"]) == ("pt_BR", "Brasil")
    assert value["Conta de Pagamento"] == "2.1.1.01 Fornecedor"
    assert value["Conta de Recebimento"] == "1.1.2.01 Clientes"
    assert value["CNAE Principal"] == "2731-7/00 - Fabricação de aparelhos"
    assert value["CNAE Principal/ID"] == "l10n_br_fiscal.cnae_2731700"
    for reserved in ("Vendedor", "Indústria principal", "Indústrias Secundárias",
                     "Latitude Geográfica", "Longitude Geográfica"):
        assert value[reserved] == ""


def test_helpers():
    assert format_phone("1133334444") == "(11) 3333-4444" and format_phone(None) == ""
    assert format_state("SP") == "São Paulo (BR)" and format_state("XX") == ""
    assert format_natureza(2135, "Empresário (Individual)") == "213-5 - Empresário (Individual)"
    long = "Fabricação de aparelhos e equipamentos para distribuição e controle de energia elétrica"
    text = cnae_text(2731700, long)
    assert len(text) == 75 and text.endswith("uição e c...")
    assert cnae_id(9511800) == "l10n_br_fiscal.cnae_9511800"


def test_site_only_on_matriz_and_missing_data_empty():
    data = raw()
    data["fontes"][1]["conteudo"]["estabelecimentos"][1]["cadastro"]["email"] = None
    rows = build_rows(data).rows
    filial = next(dict(zip(COLUMNS, r)) for r in rows if r[0] == "Acme Tecnologia Ltda" and r[1].endswith("0002-62"))
    assert filial["Site"] == "" and filial["E-mail"] == ""


def test_old_run_without_full_branch_data_keeps_only_matriz_with_warning():
    data = raw()
    for est in data["fontes"][1]["conteudo"]["estabelecimentos"]:
        est.pop("cadastro")
    result = build_rows(data)
    assert result.contatos == 1 and any("execução antiga" in a for a in result.avisos)
    assert build_rows(raw(filiais=False)).contatos == 1


def test_cnpj_source_not_ok_raises():
    with pytest.raises(ContatosError, match="falhou"):
        build_rows(raw(cnpj_status="falha"))


# ---- ajustes


def write_ajustes(tmp_path, content):
    path = tmp_path / "contatos-ajustes-2026-09-30_100000.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_adjustment_fills_vendedor_and_keeps_rest(tmp_path):
    path = write_ajustes(tmp_path, f'''"{mask_cnpj(MATRIZ)}":
  vendedor: {{valor: "Fernando Colus", fonte: "ata.md: o comercial é o Fernando"}}
''')
    avisos = []
    ajustes = load_ajustes(path, avisos)
    rows = build_rows(raw(filiais=False), ajustes).rows
    value = dict(zip(COLUMNS, rows[0]))
    assert value["Vendedor"] == "Fernando Colus" and value["Razão Social"] == "Acme Tecnologia Ltda"
    assert avisos == []


def test_adjustment_ignores_protected_columns_missing_source_and_unknown_cnpj(tmp_path):
    path = write_ajustes(tmp_path, f'''"{mask_cnpj(MATRIZ)}":
  razao_social: {{valor: "Outra", fonte: "x"}}
  cnae: {{valor: "1", fonte: "x"}}
  industria_principal: {{valor: "TI/Comunicação"}}
"99.999.999/0001-99":
  vendedor: {{valor: "Ana", fonte: "x"}}
''')
    avisos = []
    ajustes = load_ajustes(path, avisos)
    result = build_rows(raw(filiais=False), ajustes)
    avisos += result.avisos
    value = dict(zip(COLUMNS, result.rows[0]))
    assert value["Razão Social"] == "Acme Tecnologia Ltda" and value["Indústria principal"] == ""
    assert sum("não ajustável" in a for a in avisos) == 2
    assert any("falta valor ou fonte" in a for a in avisos)
    assert any("não está no CSV" in a for a in avisos)


# ---- arquivos e CLI


def test_export_never_overwrites(tmp_path):
    run = tmp_path / "2026-09-30_100000-acme"
    run.mkdir()
    (run / "raw.json").write_text(json.dumps(raw()), encoding="utf-8")
    now = datetime(2026, 9, 30, 11, 0, 0)
    first, _ = export(run, tmp_path / "out", now=now)
    second, _ = export(run, tmp_path / "out", now=now)
    assert first != second and first.exists() and second.exists()
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")


def test_find_latest_run_matches_exact_client(tmp_path):
    for name in ("2026-09-25_100000-ar", "2026-09-26_100000-estilo-ar", "2026-09-27_100000-ar"):
        (tmp_path / name).mkdir()
    assert find_latest_run(tmp_path, "ar").name == "2026-09-27_100000-ar"
    assert find_latest_run(tmp_path, "estilo-ar").name == "2026-09-26_100000-estilo-ar"
    with pytest.raises(ContatosError):
        find_latest_run(tmp_path, "zzz")


def test_cli_end_to_end(tmp_path, capsys):
    run = tmp_path / "reports" / "2026-09-30_100000-acme"
    run.mkdir(parents=True)
    (run / "raw.json").write_text(json.dumps(raw()), encoding="utf-8")
    out = tmp_path / "discovery"
    with pytest.raises(SystemExit) as exc:
        main(["contatos", "--client", "acme", "--reports-dir", str(tmp_path / "reports"),
              "--out-dir", str(out)])
    assert exc.value.code == 0
    files = list((out / "acme").glob("contatos-*.csv"))
    assert len(files) == 1
    lines = files[0].read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith('"Razão Social","ID do Imposto"')
    assert "2026-09-30_100000-acme" in capsys.readouterr().out


def test_cli_fails_without_cnpj(tmp_path, capsys):
    run = tmp_path / "reports" / "2026-09-30_100000-acme"
    run.mkdir(parents=True)
    (run / "raw.json").write_text(json.dumps(raw(cnpj_status="falha")), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        main(["contatos", "--client", "acme", "--reports-dir", str(tmp_path / "reports"),
              "--out-dir", str(tmp_path / "discovery")])
    assert exc.value.code == 1
    assert not (tmp_path / "discovery").exists()
