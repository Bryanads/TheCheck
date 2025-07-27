fetch('/data/previsoes.json')
  .then(response => response.json())
  .then(data => {
    const container = document.getElementById('conteudo');
    container.innerHTML = '';

    const nomePraia = Object.keys(data)[0];
    const previsoes = data[nomePraia];

    const titulo = document.createElement('h2');
    titulo.textContent = `🌊 Praia: ${nomePraia}`;
    container.appendChild(titulo);

    Object.entries(previsoes).forEach(([dia, infoDia]) => {
      const divDia = document.createElement('div');
      divDia.className = 'dia';

      const h3 = document.createElement('h3');
      h3.textContent = `📅 ${dia}`;
      divDia.appendChild(h3);

      // Renderizar cada hora, ignorando "tides"
      Object.entries(infoDia).forEach(([hora, dados]) => {
        if (hora === 'tides') return;

        const divHora = document.createElement('div');
        divHora.className = 'hora';

        const tituloHora = document.createElement('strong');
        tituloHora.textContent = `🕒 ${hora}`;
        divHora.appendChild(tituloHora);

        const ul = document.createElement('ul');
        Object.entries(dados).forEach(([param, valor]) => {
          const li = document.createElement('li');
          li.textContent = `${param}: ${typeof valor === 'number' ? valor.toFixed(2) : valor}`;
          ul.appendChild(li);
        });

        divHora.appendChild(ul);
        divDia.appendChild(divHora);
      });

      // Mostrar marés (corrigido para garantir array)
      const tides = Array.isArray(infoDia.tides) ? infoDia.tides : [];
      if (tides.length > 0) {
        const tideDiv = document.createElement('div');
        tideDiv.className = 'tide';
        tideDiv.innerHTML = `<strong>🌊 Marés:</strong><br>` +
          tides.map(t => `${t.time} - ${t.type === 'high' ? 'Alta' : 'Baixa'} (${t.height.toFixed(2)} m)`).join('<br>');
        divDia.appendChild(tideDiv);
      }

      container.appendChild(divDia);
    });
  })
  .catch(error => {
    document.getElementById('conteudo').textContent = 'Erro ao carregar os dados.';
    console.error(error);
  });