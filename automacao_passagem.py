import asyncio
# Test commit to verify GitHub connection
from playwright.async_api import async_playwright, expect
import os # Importar os para path do screenshot
from datetime import datetime # Importar datetime para nome único

async def run():
    async with async_playwright() as p:
        # browser = await p.chromium.launch(headless=False)
        browser = await p.chromium.launch()
        page = await browser.new_page()

        url = "https://queropassagem.com.br/onibus/cruzeiro-sp-para-sao-paulo-sp?partida=16/04/2025&chegada=16/04/2025"
        print(f"Navegando para: {url}")
        try:
            # Espera a página carregar, pode ser 'domcontentloaded' para ser mais rápido antes de checar cookies
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            print("Página carregada (domcontentloaded). Verificando cookies...")

            # Tentar fechar banner de cookies (ajuste o seletor se necessário)
            try:
                # Seletores comuns para botões de aceitar cookies
                cookie_button_selector = 'button:has-text("Aceitar"), button:has-text("Concordo"), button:has-text("OK"), #lgpd-accept'
                cookie_button = page.locator(cookie_button_selector).first # Pega o primeiro que encontrar
                print("Tentando encontrar e clicar no botão de aceitar cookies...")
                await cookie_button.click(timeout=5000) # Timeout curto, se não achar rápido, provavelmente não tem
                print("Botão de cookies clicado (ou não encontrado).")
                # Esperar um pouco para o banner sumir e o conteúdo ajustar
                await page.wait_for_timeout(1000)
            except Exception as cookie_error:
                print(f"Não foi possível clicar no botão de cookies (pode não existir): {cookie_error}")

            # Agora espera a rede ficar ociosa após possivelmente fechar o cookie banner
            print("Esperando a rede ficar ociosa após verificação de cookies...")
            await page.wait_for_load_state('networkidle', timeout=45000)
            print("Rede ociosa.")

        except Exception as e:
            print(f"Erro ao carregar a URL inicial ou lidar com cookies: {e}")
            # Adicionar screenshot aqui também seria útil
            screenshot_folder = "screenshots"
            if not os.path.exists(screenshot_folder): os.makedirs(screenshot_folder)
            screenshot_path = os.path.join(screenshot_folder, f"erro_goto_cookies_{datetime.now():%Y%m%d_%H%M%S}.png")
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
            await browser.close()
            return

        # --- IDA ---
        print("Procurando passagem de IDA às 06:15...")
        # Seletor direto para a div.linha usando o atributo data
        ida_linha_selector = 'div.linha[data="2025-04-16T06:15:00-03:00"]'
        ida_linha_locator = page.locator(ida_linha_selector)
        # Seletor para o botão DENTRO da linha específica
        escolher_ida_button = ida_linha_locator.locator('input.submit[value="ESCOLHER IDA"]')

        try:
            print(f"Tentando localizar a linha IDA: {ida_linha_selector}")
            # Espera a linha existir no DOM
            await expect(ida_linha_locator).to_be_attached(timeout=30000) # Aumentar timeout se a página demorar muito
            print("Linha IDA (06:15) encontrada no DOM. Rolando para visualizá-la...")
            # Rola a página até que a linha esteja visível
            await ida_linha_locator.scroll_into_view_if_needed()
            print("Linha IDA (06:15) agora visível.")

            # Agora que está visível, espera o botão estar habilitado e clica
            print("Tentando localizar e clicar no botão 'ESCOLHER IDA'...")
            await expect(escolher_ida_button).to_be_enabled(timeout=10000) # Esperar estar clicável
            print("Botão 'ESCOLHER IDA' encontrado e habilitado. Clicando...")
            await escolher_ida_button.click()
            print("Botão 'ESCOLHER IDA' clicado.")

        except Exception as e:
            print(f"Erro ao localizar/rolar/clicar na passagem IDA (06:15): {e}")
            print(f"Verifique se a linha com seletor '{ida_linha_selector}' existe e contém o botão esperado.")
            # Tirar screenshot no momento do erro
            screenshot_folder = "screenshots"
            if not os.path.exists(screenshot_folder): os.makedirs(screenshot_folder)
            screenshot_path = os.path.join(screenshot_folder, f"erro_botao_ida_{datetime.now():%Y%m%d_%H%M%S}.png")
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
            await browser.close()
            return

        # --- Seleção de Poltronas ---
        print("Selecionando poltronas...")
        # Aumentar a espera aqui, pois a tela de poltronas pode demorar
        await page.wait_for_load_state('networkidle', timeout=90000)

        # --- Poltrona IDA (Número 11) ---
        try:
            print("Selecionando poltrona 11 (IDA)...")
            # Esperar por um elemento distintivo do mapa de assentos - USANDO PISTAS DO SELETOR JS
            # Tenta encontrar o container específico do ônibus IDA dentro do elemento #trecho
            mapa_assentos_ida_locator = page.locator('#trecho .onibus.IDA').first
            print(f"Esperando pelo container do mapa IDA: '#trecho .onibus.IDA'")
            await expect(mapa_assentos_ida_locator).to_be_visible(timeout=60000)
            print("Container do mapa de assentos IDA visível.")

            # >>> NOVA ABORDAGEM: Encontrar pelo texto "11" diretamente <<<
            # Procura por um elemento dentro do mapa que contenha o texto "11"
            poltrona_11_locator = mapa_assentos_ida_locator.locator('text=11') # Shorthand do Playwright para texto visível

            print("Procurando pela poltrona 11 visível...")
            await expect(poltrona_11_locator).to_be_visible(timeout=15000)
            print("Poltrona 11 encontrada.")
            await poltrona_11_locator.scroll_into_view_if_needed() # Garante visibilidade

            # >>> VERIFICAÇÃO ADICIONAL: Checar se está desabilitada <<<
            # Avalia no navegador se o elemento tem classes comuns de indisponibilidade
            is_disabled_or_occupied = await poltrona_11_locator.evaluate('''
                element => {
                    const checkClasses = (el) =>
                        el.classList.contains("disabled") ||
                        el.classList.contains("seat-disabled") ||
                        el.classList.contains("occupied") ||
                        el.classList.contains("seat-occupied") ||
                        el.hasAttribute("disabled");
                    // Verifica o próprio elemento e o pai imediato
                    return checkClasses(element) || (element.parentElement && checkClasses(element.parentElement));
                }
            ''')

            if is_disabled_or_occupied:
                raise Exception("Poltrona 11 encontrada, mas parece estar desabilitada ou ocupada.")
            else:
                print("Poltrona 11 parece estar disponível. Clicando...")
                await poltrona_11_locator.click()
                print("Poltrona 11 selecionada.")

            # Botão Confirmar (mantém o seletor anterior, ajuste se necessário)
            confirmar_ida_button = page.locator('button:text-matches("Confirmar", "i"), button:has-text("Prosseguir"), button:has-text("Avançar"), button:has-text("Confirmar poltrona")').first
            await expect(confirmar_ida_button).to_be_enabled(timeout=15000)
            await confirmar_ida_button.click()
            print("Confirmação da poltrona IDA clicada.")
            await page.wait_for_load_state('networkidle', timeout=45000) # Espera após confirmar

        except Exception as e:
            print(f"Erro ao selecionar a poltrona 11 (IDA): {e}")
            screenshot_folder = "screenshots"
            if not os.path.exists(screenshot_folder): os.makedirs(screenshot_folder)
            screenshot_path = os.path.join(screenshot_folder, f"erro_poltrona_ida_{datetime.now():%Y%m%d_%H%M%S}.png")
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
            await browser.close()
            return

        # --- Poltrona VOLTA (Número 15) ---
        # Esta seção precisa ser implementada após confirmar a poltrona IDA
        # O fluxo exato (vai para o mapa de volta? Pede para escolher passagem de volta?) precisa ser determinado
        try:
            print("Selecionando poltrona 15 (VOLTA)...")
            # Esperar pela seção/mapa de volta (AJUSTE O SELETOR CONFORME NECESSÁRIO)
            mapa_assentos_volta_locator = page.locator(':text("Escolha sua poltrona de volta"), .seatmap-return, .seats-trip--return, #trecho .onibus.VOLTA').first # Adicionado seletor similar ao IDA
            print(f"Esperando pelo container/título do mapa VOLTA...")
            await expect(mapa_assentos_volta_locator).to_be_visible(timeout=60000) # Aumentar timeout
            print("Mapa de assentos VOLTA visível.")

            # Encontrar poltrona 15 (mesma lógica da IDA, mas dentro do mapa de VOLTA)
            poltrona_volta_map_container = mapa_assentos_volta_locator # Assumindo que o locator acima é o container
            # Se o locator for apenas um título, precisaremos de um seletor para o container real
            # Ex: poltrona_volta_map_container = page.locator('#trecho .onibus.VOLTA').first OU similar

            poltrona_15_locator = poltrona_volta_map_container.locator('text=15')

            print("Procurando pela poltrona 15 visível...")
            await expect(poltrona_15_locator).to_be_visible(timeout=15000)
            print("Poltrona 15 encontrada.")
            await poltrona_15_locator.scroll_into_view_if_needed() # Garante visibilidade

            is_disabled_or_occupied_volta = await poltrona_15_locator.evaluate('''
                element => { /* Mesma função JS da IDA */ }
            ''') # Simplificado aqui, mas use a mesma função JS

            if is_disabled_or_occupied_volta:
                 raise Exception("Poltrona 15 encontrada, mas parece estar desabilitada ou ocupada.")
            else:
                print("Poltrona 15 parece estar disponível. Clicando...")
                await poltrona_15_locator.click()
                print("Poltrona 15 selecionada.")


            # Botão Confirmar (AJUSTE O SELETOR CONFORME NECESSÁRIO)
            confirmar_volta_button = page.locator('button:text-matches("Confirmar", "i"), button:has-text("Prosseguir"), button:has-text("Avançar"), button:has-text("Confirmar poltrona")').first
            await expect(confirmar_volta_button).to_be_enabled(timeout=15000)
            await confirmar_volta_button.click()
            print("Confirmação da poltrona VOLTA clicada.")
            await page.wait_for_load_state('networkidle', timeout=45000)

        except Exception as e:
            print(f"Erro ao selecionar a poltrona 15 (VOLTA): {e}")
            screenshot_folder = "screenshots"
            if not os.path.exists(screenshot_folder): os.makedirs(screenshot_folder)
            screenshot_path = os.path.join(screenshot_folder, f"erro_poltrona_volta_{datetime.now():%Y%m%d_%H%M%S}.png")
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
            await browser.close()
            return

        # --- Finalizar ---
        try:
            print("Procurando botão para finalizar...")
             # Seletor mais específico se possível (ex: ID, data-testid)
             # Tentar localizar botão comum de checkout/pagamento
            finalizar_button = page.locator('button:has-text("Ir para pagamento"), button:has-text("Finalizar Compra"), button:has-text("Avançar para pagamento"), #submit-button, [data-testid="checkout-button"], [data-cy="payment-button"]').first
            await expect(finalizar_button).to_be_visible(timeout=45000) # Aumentar timeout
            print("Botão final encontrado. Clicando...")
            # await finalizar_button.click()
            print("Simulação: Clicaria no botão final aqui.")

        except Exception as e:
             print(f"Erro ao encontrar ou clicar no botão final: {e}")
             screenshot_folder = "screenshots"
             if not os.path.exists(screenshot_folder): os.makedirs(screenshot_folder)
             screenshot_path = os.path.join(screenshot_folder, f"erro_botao_final_{datetime.now():%Y%m%d_%H%M%S}.png")
             await page.screenshot(path=screenshot_path)
             print(f"Screenshot salvo em: {screenshot_path}")
             # await browser.close() # Manter aberto para inspeção se falhar aqui
             # return

        print("Tarefa de automação concluída (ou chegou ao ponto final definido).")
        await asyncio.sleep(5)
        await browser.close()

async def main():
    await run()

if __name__ == "__main__":
    # Cria a pasta screenshots no diretório atual se não existir
    screenshot_dir = "screenshots"
    if not os.path.exists(screenshot_dir):
        try:
            os.makedirs(screenshot_dir)
            print(f"Diretório '{screenshot_dir}' criado.")
        except OSError as e:
            print(f"Erro ao criar diretório '{screenshot_dir}': {e}")
            # Decide se quer parar ou continuar sem screenshots
            # Por enquanto, apenas imprime o erro

    asyncio.run(main()) 
