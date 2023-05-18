import React, { useState } from 'react';
import './App.css';
import Watchlist from './Watchlist';
import SaleItems from './SaleItems';

function App() {
  const [starredItems, setStarredItems] = useState([]);
  const handleStarClick = (item) => {
    if (starredItems.some((starredItem) => starredItem.id === item.id)) {
      setStarredItems((prevStarredItems) =>
        prevStarredItems.filter((starredItem) => starredItem.id !== item.id)
      );
    } else {
      setStarredItems((prevStarredItems) => [...prevStarredItems, item]);
    }
  };
  return (
    <div className="App">
      <h1>Sale Items</h1>
      <SaleItems starredItems={starredItems} handleStarClick={handleStarClick} />
      <Watchlist
        starredItems={starredItems}
        handleStarClick={handleStarClick}
      />
    </div>
  );
}

export default App;
