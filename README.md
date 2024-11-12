# Relatório PBL 2 - TEC 502 - MI-Concorrência e Conectividade
Antônio Felipe Ferreira de Jesus Moreira
UEFS - 23 de setembro de 2024
email: felipetompsomf18@gmail.com
# Resumo(Abstract)
**Resumo**
Este projeto apresenta uma solução para a venda de passagens distribuída entre diferentes servidores de companhias aéreas, aplicando uma arquitetura de comunicação cliente-servidor distribuída. Os servidores de cada companhia mantêm informações sobre rotas e passagens, interligando-se por meio de APIs para verificar a disponibilidade de trechos e realizar vendas em tempo real. Para garantir consistência e exclusividade nas compras, foi implementado um mecanismo de exclusão mútua distribuída com base no algoritmo Ricart-Agrawala, prevenindo conflitos e garantindo que cada trecho seja adquirido apenas uma vez. Além disso, os servidores compartilham as rotas disponíveis com os clientes, que escolhem as passagens com base em uma lista consolidada de todas as companhias participantes. Utilizando Docker para contaneirização, o sistema facilita a execução em diferentes ambientes, garantindo replicação e simplificando testes de desempenho e concorrência em larga escala. O projeto documenta o desenvolvimento completo, incluindo código no GitHub, com explicações sobre as principais funções e testes automatizados para assegurar confiabilidade e robustez da solução.
# Introdução
Este projeto apresenta uma solução distribuída para a venda de passagens entre diferentes companhias aéreas utilizando uma rede de servidores distribuídos. Com o uso de APIs REST para comunicação entre os servidores e com os clientes, o sistema busca garantir a disponibilidade, a consistência dos dados e o controle de concorrência, essencial para que uma passagem não seja vendida mais de uma vez. Além disso, a arquitetura foi desenvolvida com suporte ao Docker, possibilitando fácil replicação e execução em ambientes isolados.
# Metodologia utilizada
1. Arquitetura da Solução
A solução utiliza uma arquitetura distribuída com três servidores, representando três companhias aéreas: Companhia A, Companhia B e Companhia C. Cada servidor é responsável por gerenciar as passagens de sua própria companhia e fornecer informações de disponibilidade e compra dos trechos sob sua administração. Essa abordagem é caracterizada como uma arquitetura cliente-servidor com múltiplos servidores.
- Servidor: Implementado em server.py, cada servidor gerencia suas rotas e coordena com os outros para validar solicitações de compra, disponibilizando APIs para que clientes e outros servidores possam consultar e adquirir passagens.
- Cliente: Em client.py, a aplicação cliente permite ao usuário escolher um servidor para interagir, exibindo rotas disponíveis e possibilitando a compra de passagens.
- Docker: Todos os componentes estão encapsulados em containers Docker, garantindo isolamento e simplicidade de execução.
2. Protocolo de Comunicação
A comunicação entre servidores e entre cliente e servidor ocorre por meio de APIs REST:
- /solicitar_acesso: O cliente solicita acesso a um trecho. O servidor coordena com outros servidores para verificar se a compra pode ser realizada. Parâmetros: cliente_id (ID do cliente).
- /resposta_solicitacao: Servidor responde à solicitação de acesso ao trecho. Parâmetros: cliente_id, sequencial.
- /verificar_disponibilidade: Permite que o cliente ou outros servidores consultem a disponibilidade de passagens para um trecho específico. Parâmetros: origem, destino.
- /realizar_compra: Usado para efetuar a compra de um trecho, decrementando o número de passagens disponíveis. Parâmetros: origem, destino.
Essas APIs garantem a coordenação entre servidores para evitar duplicidade de vendas e permitem o compartilhamento de informações entre diferentes companhias.
3. Roteamento
O cálculo de rotas utiliza a função gerar_rotas(cidades), que cria um conjunto de rotas distribuídas entre as cidades disponíveis, com percursos intermediários variáveis. O sistema exibe ao cliente todas as rotas possíveis, incluindo as rotas disponíveis nas outras companhias por meio de consultas às APIs. Essa abordagem permite que o cliente tenha uma visão abrangente das opções de passagem, independentemente da companhia que escolheu inicialmente.
4. Concorrência Distribuída
Para garantir que uma passagem não seja vendida mais de uma vez, o sistema utiliza o algoritmo de exclusão mútua distribuída de Ricart-Agrawala. Cada servidor gerencia um controle de acesso aos trechos por meio de requisições sequenciais que são registradas e processadas em todos os servidores, assegurando que apenas um cliente possa comprar uma passagem específica em um dado momento.
