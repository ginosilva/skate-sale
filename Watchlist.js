import React from 'react';
import SaleItemComponent from './SaleItem';
import './Watchlist.css';

const Watchlist = ({ starredItems, handleStarClick }) => {
  return (
    <div className="watchlist">
      <h2>Watchlist</h2>
      <div className="watchlist-items">
        {starredItems.map((item) => (
          <div key={item.id} className="watchlist-item">
            <SaleItemComponent
              item={item}
              handleStarClick={handleStarClick}
              isStarred
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default Watchlist;
