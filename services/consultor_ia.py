import os
import json
from typing import List, Dict
from django.conf import settings
from apps.inventory.models import Part

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except (ImportError, TypeError):
    GEMINI_AVAILABLE = False


class ConsultorIA:
    def __init__(self):
        self.use_gemini = False
        if GEMINI_AVAILABLE:
            api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel("gemini-pro")
                    self.use_gemini = True
                except Exception:
                    self.use_gemini = False

    def processar_query(self, user_query: str) -> Dict:
        interpretacao = self._extrair_intencao(user_query)
        from services.vector_search_service import get_vector_search_service
        search_service = get_vector_search_service()
        peças_encontradas = search_service.search_parts_by_query(user_query, top_k=10)
        resposta = self._gerar_resposta_consultor(
            user_query,
            peças_encontradas,
            interpretacao.get("intenção", "")
        )

        return {
            "query": user_query,
            "intenção": interpretacao.get("intenção", ""),
            "resposta": resposta,
            "peças_recomendadas": peças_encontradas,
            "tokens_usados": 0,
            "sucesso": True
        }

    def _extrair_intencao(self, user_query: str) -> Dict:
        if self.use_gemini:
            return self._extrair_intencao_gemini(user_query)
        else:
            return self._extrair_intencao_fallback(user_query)

    def _extrair_intencao_gemini(self, user_query: str) -> Dict:
        prompt = f"""Você é um assistente para um marketplace de autopeças. 
        
Um usuário fez esta pergunta: "{user_query}"

Extraia:
1. A INTENÇÃO: que tipo de peça ele procura? (ex: motor, turbo, filtro, pastilha de freio, etc.)
2. PALAVRAS-CHAVE: liste 3-5 termos relacionados à peça procurada
3. SINONÍMIA: liste possíveis nomes alternativos ou similares para essa peça

Responda em JSON sem markdown:
{{"intenção": "...", "palavras-chave": [...], "sinônimos": [...]}}"""

        try:
            response = self.model.generate_content(prompt)
            interpretacao_text = response.text
            
            if "```json" in interpretacao_text:
                json_str = interpretacao_text.split("```json")[1].split("```")[0].strip()
            elif "{" in interpretacao_text:
                json_str = interpretacao_text[interpretacao_text.find("{"):interpretacao_text.rfind("}")+1]
            else:
                json_str = interpretacao_text
                
            return json.loads(json_str)
        except Exception:
            return self._extrair_intencao_fallback(user_query)

    def _extrair_intencao_fallback(self, user_query: str) -> Dict:
        palavras_chave = user_query.lower().split()
        sinonimos_map = {
            "motor": ["motor", "engine", "v8", "v6", "cilindro"],
            "turbo": ["turbo", "turbocharger", "compressor"],
            "filtro": ["filtro", "filter", "elemento", "plissado"],
            "pastilha": ["pastilha", "plaqueta", "freio", "brake pad"],
            "óleo": ["óleo", "oil", "lubrificante"],
            "pneu": ["pneu", "tire", "pneus"],
            "bateria": ["bateria", "battery", "acumulador"],
        }
        intenção = "peça de automóvel"
        sinonimos = []
        for categoria, termos in sinonimos_map.items():
            if any(termo in palavras_chave for termo in termos):
                intenção = categoria
                sinonimos = termos
                break
        return {
            "intenção": intenção,
            "palavras-chave": palavras_chave[:5],
            "sinônimos": sinonimos
        }

    def _buscar_peças_com_sinonímia(self, palavras_chave: List[str]) -> List[Dict]:
        peças_score = {}  # {part_id: score}
        for palavra in palavras_chave:
            parts = Part.objects.filter(
                name__icontains=palavra,
                quantity__gt=0
            )
            for part in parts:
                peças_score[part.id] = peças_score.get(part.id, 0) + 10
        for palavra in palavras_chave:
            parts = Part.objects.filter(
                description__icontains=palavra,
                quantity__gt=0
            )
            for part in parts:
                peças_score[part.id] = peças_score.get(part.id, 0) + 5
        peças_ordenadas = []
        for part_id, score in sorted(peças_score.items(), key=lambda x: x[1], reverse=True):
            try:
                part = Part.objects.get(id=part_id)
                peças_ordenadas.append({
                    "id": part.id,
                    "nome": part.name,
                    "descrição": part.description,
                    "preço": str(part.price),
                    "quantidade": part.quantity,
                    "score": score
                })
            except Part.DoesNotExist:
                pass

        return peças_ordenadas[:10]

    def _gerar_resposta_consultor(self, query: str, peças: List[Dict], intenção: str) -> str:
        if not peças:
            return f"Desculpe, não encontrei peças relacionadas a '{intenção}'. Poderia descrever melhor o que procura?"

        if self.use_gemini:
            return self._gerar_resposta_gemini(query, peças, intenção)
        else:
            return self._gerar_resposta_fallback(peças, intenção)

    def _gerar_resposta_gemini(self, query: str, peças: List[Dict], intenção: str) -> str:
        """Gera resposta com Gemini."""
        peças_formatadas = "\n".join([
            f"- {p['name']}: {p['description']} | R$ {p['price']} | {p['quantity']} em estoque (relevância: {p.get('similarity_score', 0):.2%})"
            for p in peças
        ])

        prompt = f"""Você é um assistente amigável de um marketplace de autopeças.

O usuário perguntou: "{query}"
Você interpretou que ele procura: "{intenção}"

As peças disponíveis são:
{peças_formatadas}

Gere uma resposta curta (2-3 frases) recomendando as peças. 
Seja amigável, mencione o preço e disponibilidade.
Não use markdown, apenas texto simples."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception:
            return self._gerar_resposta_fallback(peças, intenção)

    def _gerar_resposta_fallback(self, peças: List[Dict], intenção: str) -> str:
        """Gera resposta simples sem IA."""
        if not peças:
            return f"Desculpe, não encontrei peças relacionadas a '{intenção}'."
        
        top_peça = peças[0]
        return f"Encontrei {len(peças)} peça(s) de '{intenção}'. A mais relevante é '{top_peça['name']}' por R$ {top_peça['price']}, com {top_peça['quantity']} unidades em estoque (relevância: {top_peça.get('similarity_score', 0):.2%})."


def processar_query_consultor(user_query: str) -> Dict:
    try:
        consultor = ConsultorIA()
        return consultor.processar_query(user_query)
    except Exception as e:
        return {
            "query": user_query,
            "intenção": "",
            "resposta": f"Erro ao processar sua pergunta: {str(e)}",
            "peças_recomendadas": [],
            "tokens_usados": 0,
            "sucesso": False,
            "erro": str(e)
        }

