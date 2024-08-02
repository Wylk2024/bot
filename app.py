from flask import Flask, request, jsonify
import os
import pandas as pd
import spacy
from fuzzywuzzy import process
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play

app = Flask(__name__)

class GroqChatbot:
  def __init__(self):
      self.df = self.carregar_df_procedimentos_medicos()
      self.nlp = spacy.load("pt_core_news_sm")

  def carregar_df_procedimentos_medicos(self):
      try:
          # Carregar o DataFrame
          df = pd.read_excel('procedimentos_medicos.xlsx', engine='openpyxl')
          return df
      except FileNotFoundError:
          print("Erro: arquivo procedimentos_medicos.xlsx não encontrado.")
          return None
      except pd.errors.ParserError:
          print("Erro: houve um problema ao analisar o arquivo Excel.")
          return None

  def obter_info_procedimento(self, consulta, indice=0):
      if self.df is None:
          return "Erro ao carregar a base de dados de procedimentos médicos."

      # Usar o modelo spaCy para NLP
      doc = self.nlp(consulta)
      # Extrair substantivos, nomes próprios e números do texto do usuário
      termos_procedimento = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN', 'NUM']]
      consulta_procedimento = ' '.join(termos_procedimento)

      # Tentar buscar pelo código primeiro
      procedimentos_por_codigo = self.df[self.df['Código'].astype(str).str.contains(consulta_procedimento, case=False, na=False)]
      if not procedimentos_por_codigo.empty:
          procedimentos = []
          for i, row in procedimentos_por_codigo.iterrows():
              codigo = row['Código']
              nome = row['Nome do procedimento']
              descricao = row['Descrição']
              info_paciente = row['Informações para o paciente']
              procedimentos.append(f"{nome} (Código: {codigo})\n\nDescrição: {descricao}\n\nInformações para o paciente: {info_paciente}")
          if indice < len(procedimentos):
              return procedimentos[indice]
          else:
              return '\n\n'.join(procedimentos)

      # Se não encontrado pelo código, tentar buscar pelo nome do procedimento
      procedimentos_por_nome = self.df[self.df['Nome do procedimento'].str.contains(consulta_procedimento, case=False, na=False)]
      if not procedimentos_por_nome.empty:
          procedimentos = []
          for i, row in procedimentos_por_nome.iterrows():
              codigo = row['Código']
              nome = row['Nome do procedimento']
              descricao = row['Descrição']
              info_paciente = row['Informações para o paciente']
              procedimentos.append(f"{nome} (Código: {codigo})\n\nDescrição: {descricao}\n\nInformações para o paciente: {info_paciente}")
          if indice < len(procedimentos):
              return procedimentos[indice]
          else:
              return '\n\n'.join(procedimentos)

      # Se não encontrado, usar correspondência aproximada
      nomes_procedimentos = self.df['Nome do procedimento'].tolist()
      melhores_correspondencias = process.extract(consulta_procedimento, nomes_procedimentos, limit=3)
      sugestoes = [correspondencia[0] for correspondencia in melhores_correspondencias if correspondencia[1] > 60]  # Ajuste o limiar conforme necessário

      if sugestoes:
          sugestoes_texto = "\n".join([f"- {sugestao}" for sugestao in sugestoes])
          return f"Desculpe, não encontrei informações exatas sobre '{consulta_procedimento}'. Você quis dizer:\n{sugestoes_texto}?"

      return "Desculpe, não encontrei informações sobre esse procedimento. Você pode tentar outro termo ou verificar a ortografia."

chatbot = GroqChatbot()

@app.route('/chatbot', methods=['POST'])
def chatbot_response():
  data = request.json
  message = data.get('message', '')
  response = chatbot.obter_info_procedimento(message)
  return jsonify({'message': response})

if __name__ == '__main__':
  app.run(debug=True)