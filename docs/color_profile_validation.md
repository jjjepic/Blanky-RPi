# Validação dos perfis cromáticos

Relatório gerado por `tools/validate_color_profiles.py` a partir de `ui/ColorVisionProfiles.js`. 
A mesma fonte de tokens é usada pelo tema QML e pelos eventos/registos renderizados em Python.

## Critérios

- Contraste de texto normal: mínimo **4.5:1** (WCAG 2.2 SC 1.4.3).
- Contraste de componentes e bordas: mínimo **3.0:1** (WCAG 2.2 SC 1.4.11).
- Separação perceptiva após simulação: DeltaE CIELAB euclidiano mínimo **15**.
- Separação em escala de cinzentos: diferença de luminância relativa mínima **0.10**.
- Simulação: modelo Machado et al. 2009, via `colorspacious`, severidade 100.

**Resultado global:** PASS (56/56 verificações aprovadas)

## Contraste WCAG

| Perfil | Verificação | Contraste | Mínimo | Resultado |
| --- | --- | ---: | ---: | --- |
| universal | Texto success / superfície success | 7.39:1 | 4.5:1 | PASS |
| universal | Borda success / superfície adjacente | 8.97:1 | 3.0:1 | PASS |
| universal | Texto warning / superfície warning | 10.41:1 | 4.5:1 | PASS |
| universal | Borda warning / superfície adjacente | 12.46:1 | 3.0:1 | PASS |
| universal | Texto error / superfície error | 4.88:1 | 4.5:1 | PASS |
| universal | Borda error / superfície adjacente | 4.80:1 | 3.0:1 | PASS |
| universal | Texto inactive / superfície inactive | 4.87:1 | 4.5:1 | PASS |
| universal | Borda inactive / superfície adjacente | 5.08:1 | 3.0:1 | PASS |
| protan | Texto success / superfície success | 7.62:1 | 4.5:1 | PASS |
| protan | Borda success / superfície adjacente | 9.35:1 | 3.0:1 | PASS |
| protan | Texto warning / superfície warning | 10.56:1 | 4.5:1 | PASS |
| protan | Borda warning / superfície adjacente | 13.78:1 | 3.0:1 | PASS |
| protan | Texto error / superfície error | 4.88:1 | 4.5:1 | PASS |
| protan | Borda error / superfície adjacente | 4.80:1 | 3.0:1 | PASS |
| protan | Texto inactive / superfície inactive | 4.87:1 | 4.5:1 | PASS |
| protan | Borda inactive / superfície adjacente | 5.08:1 | 3.0:1 | PASS |
| deutan | Texto success / superfície success | 6.41:1 | 4.5:1 | PASS |
| deutan | Borda success / superfície adjacente | 7.78:1 | 3.0:1 | PASS |
| deutan | Texto warning / superfície warning | 8.57:1 | 4.5:1 | PASS |
| deutan | Borda warning / superfície adjacente | 11.04:1 | 3.0:1 | PASS |
| deutan | Texto error / superfície error | 4.88:1 | 4.5:1 | PASS |
| deutan | Borda error / superfície adjacente | 4.80:1 | 3.0:1 | PASS |
| deutan | Texto inactive / superfície inactive | 4.87:1 | 4.5:1 | PASS |
| deutan | Borda inactive / superfície adjacente | 5.08:1 | 3.0:1 | PASS |
| tritan | Texto success / superfície success | 12.31:1 | 4.5:1 | PASS |
| tritan | Borda success / superfície adjacente | 16.57:1 | 3.0:1 | PASS |
| tritan | Texto warning / superfície warning | 8.08:1 | 4.5:1 | PASS |
| tritan | Borda warning / superfície adjacente | 9.92:1 | 3.0:1 | PASS |
| tritan | Texto error / superfície error | 5.43:1 | 4.5:1 | PASS |
| tritan | Borda error / superfície adjacente | 6.21:1 | 3.0:1 | PASS |
| tritan | Texto inactive / superfície inactive | 4.80:1 | 4.5:1 | PASS |
| tritan | Borda inactive / superfície adjacente | 5.08:1 | 3.0:1 | PASS |

## Estados após simulação

| Perfil | Simulação | Par de estados | DeltaE | Delta de cinzentos | Resultado |
| --- | --- | --- | ---: | ---: | --- |
| universal | protanomaly | Sucesso / erro | 48.2 | 0.358 | PASS |
| universal | protanomaly | Sucesso / inativo | 32.3 | 0.279 | PASS |
| universal | protanomaly | Aviso / erro | 62.7 | 0.452 | PASS |
| universal | protanomaly | ON / OFF | 32.3 | 0.279 | PASS |
| universal | deuteranomaly | Sucesso / erro | 63.5 | 0.169 | PASS |
| universal | deuteranomaly | Sucesso / inativo | 35.2 | 0.194 | PASS |
| universal | deuteranomaly | Aviso / erro | 45.2 | 0.442 | PASS |
| universal | deuteranomaly | ON / OFF | 35.2 | 0.194 | PASS |
| universal | tritanomaly | Sucesso / erro | 112.4 | 0.274 | PASS |
| universal | tritanomaly | Sucesso / inativo | 39.9 | 0.257 | PASS |
| universal | tritanomaly | Aviso / erro | 52.2 | 0.400 | PASS |
| universal | tritanomaly | ON / OFF | 39.9 | 0.257 | PASS |
| protan | protanomaly | Sucesso / erro | 45.2 | 0.380 | PASS |
| protan | protanomaly | Sucesso / inativo | 29.6 | 0.301 | PASS |
| protan | protanomaly | Aviso / erro | 70.0 | 0.537 | PASS |
| protan | protanomaly | ON / OFF | 29.6 | 0.301 | PASS |
| deutan | deuteranomaly | Sucesso / erro | 59.6 | 0.108 | PASS |
| deutan | deuteranomaly | Sucesso / inativo | 30.6 | 0.133 | PASS |
| deutan | deuteranomaly | Aviso / erro | 49.8 | 0.359 | PASS |
| deutan | deuteranomaly | ON / OFF | 30.6 | 0.133 | PASS |
| tritan | tritanomaly | Sucesso / erro | 83.8 | 0.648 | PASS |
| tritan | tritanomaly | Sucesso / inativo | 40.4 | 0.672 | PASS |
| tritan | tritanomaly | Aviso / erro | 38.5 | 0.217 | PASS |
| tritan | tritanomaly | ON / OFF | 40.4 | 0.672 | PASS |

## Leitura visual

A janela **Perfis de Daltonismo** inclui uma matriz de estados de exemplo. A demonstração mantém o símbolo e o texto do estado, para que nenhum estado dependa apenas da cor.

Este relatório é uma verificação técnica de design e não um diagnóstico de visão cromática nem uma certificação legal.
