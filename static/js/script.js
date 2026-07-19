window.addEventListener('DOMContentLoaded', () => {
  
  fetch('/api/get-options')
    .then(response => response.json())
    .then(dataList => {
      // ❶ さっき作った datalist を捕まえる！
      const dataListTag = document.getElementById('pokemon-options');
      dataListTag.innerHTML = ''; // 中身を一度クリア

      // ❷ Pythonから届いた配列をループ処理
      dataList.forEach(item => {
        const optionTag = document.createElement('option');
        
        // 💡 datalistの場合、valueに「画面に見せたい文字」を入れます。
        // こうすると、入力欄に日本語名（例：ブリジュラス）が綺麗に表示・検索されます！
        optionTag.value = item.name; 
        
        // （オプション）裏でIDも持たせたい場合は、data属性という引き出しにしまっておけます
        optionTag.setAttribute('data-id', item.id);
        
        dataListTag.appendChild(optionTag); // リストの中に追加！
      });
    })
    .catch(error => {
      console.error("通信に失敗しました:", error);
    });
});
document.getElementById('pokemon-input').addEventListener('input', () => {
  const selectedValue = document.getElementById('pokemon-input').value;
  const selectedOption  = document.querySelector(`#pokemon-options option[value="${selectedValue}"]`);
  if (selectedOption) {
    const id = selectedOption.getAttribute('data-id');
    console.log('選択されたID:', id);
  }
});