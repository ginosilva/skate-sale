import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SaleItems.css';
import SaleItem from './SaleItem';

const extractStoreNameFromUrl = (url) => {
  const hostname = new URL(url).hostname;
  return hostname.split('.')[1];
};

const storeCurrency = {
  // ...storeCurrency data
};

const getCurrencySymbol = (storeName) => {
  return storeCurrency[storeName] || '£';
};

const calculateDiscount = (price, compareAtPrice) => {
  const discount = ((compareAtPrice - price) / compareAtPrice) * 100;
  return discount.toFixed(1);
};

const groupItemsByStore = (items) => {
  return items.reduce((acc, item) => {
    const storeName = extractStoreNameFromUrl(item.product_url);
    if (!acc[storeName]) {
      acc[storeName] = [];
    }
    acc[storeName].push(item);
    return acc;
  }, {});
};

const mergeItemsWithDifferentSizes = (items) => {
  const mergedItems = [];

  items.forEach((item) => {
    const existingItem = mergedItems.find(
      (mergedItem) =>
        mergedItem.title === item.title &&
        mergedItem.vendor === item.vendor &&
        mergedItem.product_type === item.product_type
    );

    if (existingItem) {
      if (!existingItem.option1.includes(item.option1)) {
        existingItem.option1.push(item.option1);
      }
    } else {
      item.option1 = [item.option1];
      mergedItems.push(item);
    }
  });

  return mergedItems;
};

const SaleItems = ({ starredItems, handleStarClick }) => {
  const [items, setItems] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [vendorFilter, setVendorFilter] = useState('');
  const [productTypeFilter, setProductTypeFilter] = useState('');
  const [sizeFilter, setSizeFilter] = useState('');
  const [displayMode, setDisplayMode] = useState('single');


  useEffect(() => {
    const fetchItems = async () => {
      try {
        const response = await axios.get('https://union-discount.herokuapp.com/items');
        const mergedItems = mergeItemsWithDifferentSizes(response.data);
        setItems(
          mergedItems.sort((a, b) => calculateDiscount(b.price, b.compare_at_price) - calculateDiscount(a.price, a.compare_at_price))
        );
        console.log('Items fetched:', items);
      } catch (error) {
        console.error('Error fetching items:', error);
      }
    };

    fetchItems();
  }, []);

  const getFilteredItems = (vendorFilter, productTypeFilter, sizeFilter) => {
    return items.filter(
      (item) =>
        (!vendorFilter || item.vendor === vendorFilter) &&
        (!productTypeFilter || item.product_type === productTypeFilter) &&
        (!sizeFilter || (Array.isArray(item.option1) && item.option1.includes(sizeFilter)))
    );
  };

  const filteredItems = getFilteredItems(vendorFilter, productTypeFilter, sizeFilter);
  const groupedItems = Object.entries(groupItemsByStore(filteredItems));
  const storeCount = groupedItems.length;

  const handleNextPage = () => {
    setCurrentPage((prevPage) => (prevPage + 1) % storeCount);
  };

  const handlePrevPage = () => {
    setCurrentPage((prevPage) => (prevPage - 1 + storeCount) % storeCount);
  };

  const uniqueVendors = Array.from(
    new Set(
      getFilteredItems('', productTypeFilter, sizeFilter).map(
        (item) => item.vendor
      )
    )
  ).sort();

  const uniqueProductTypes = Array.from(
    new Set(
      getFilteredItems(vendorFilter, '', sizeFilter).map(
        (item) => item.product_type
      )
    )
  ).sort();

  const uniqueSizes = Array.from(
    new Set(
      getFilteredItems(vendorFilter, productTypeFilter, '').flatMap(
        (item) => item.option1
      )
    )
  ).sort();

  const toggleDisplayMode = () => {
    setDisplayMode((prevDisplayMode) =>
      prevDisplayMode === 'single' ? 'all' : 'single'
    );
  };
  const renderStoreGroup = ([storeName, storeItems]) => (
    <div key={storeName}>
      <h2>{storeName}</h2>
      <div className="store-items">
        {storeItems.map((item) => (
          <SaleItem
            key={item.id}
            item={item}
            handleStarClick={handleStarClick}
            isStarred={starredItems.some((starredItem) => starredItem.id === item.id)}
          />
        ))}
      </div>
    </div>
  );
  
  return (
    <div className="sale-items">
      <div className="filters">
        <label htmlFor="vendor-filter">Vendor:</label>
        <select id="vendor-filter" value={vendorFilter} onChange={(e) => setVendorFilter(e.target.value)}>
          <option value="">All</option>
          {uniqueVendors.map((vendor) => (
            <option key={vendor} value={vendor}>{vendor}</option>
          ))}
        </select>
        <label htmlFor="product-type-filter">Product Type:</label>
        <select id="product-type-filter" value={productTypeFilter} onChange={(e) => setProductTypeFilter(e.target.value)}>
          <option value="">All</option>
          {uniqueProductTypes.map((productType) => (
            <option key={productType} value={productType}>{productType}</option>
          ))}
        </select>
        <label htmlFor="size-filter">Size:</label>
        <select id="size-filter" value={sizeFilter} onChange={(e) => setSizeFilter(e.target.value)}>
          <option value="">All</option>
          {uniqueSizes.map((size) => (
            <option key={size} value={size}>{size}</option>
          ))}
        </select>
      </div>
      {displayMode === 'single'
        ? groupedItems.slice(currentPage, currentPage + 1).map(renderStoreGroup)
        : groupedItems.map(renderStoreGroup)}

      <div className="pagination">
        <button onClick={handlePrevPage}>Previous Store</button>
        <button onClick={handleNextPage}>Next Store</button>
        <button onClick={toggleDisplayMode}>
          {displayMode === 'single' ? 'Show All Stores' : 'Show Single Store'}
        </button>
      </div>
    </div>
  );
};

export default SaleItems;