// 1. 🚀 まずは全体を縦に3等分（33.3% ずつ）に切り分ける！
Split(['#left-pane', '#middle-pane', '#right-pane'], {
    sizes: [33.3, 33.3, 33.3], // 初期の幅（%）
    minSize: 150,              // 最小幅（px）
    gutterSize: 10,            // 仕切り線の太さ（px）
    direction: 'horizontal',   // 左右に分割するモード
});

// 2. 🚀 次に、真ん中の箱（#middle-pane）の中身を上下（50% ずつ）に切り分ける！
Split(['#mid-top', '#mid-bottom'], {
    sizes: [50, 50],           // 初期の高さ（%）
    minSize: 100,              // 最小の高さ（px）
    gutterSize: 10,            // 仕切り線の太さ（px）
    direction: 'vertical',     // 上下に分割するモード
});