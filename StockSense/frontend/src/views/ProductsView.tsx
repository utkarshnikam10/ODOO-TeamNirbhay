import React, { useState } from 'react';
import { Plus, Search, FilterX, Package, Eye, ArrowRightLeft, SlidersHorizontal } from 'lucide-react';
import { useInventory } from '../context/InventoryContext';
import { Product } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { ProductFormModal } from '../components/products/ProductFormModal';
import { ProductDetailModal } from '../components/products/ProductDetailModal';
import { TransferFormModal } from '../components/transfers/TransferFormModal';
import { AdjustmentFormModal } from '../components/adjustments/AdjustmentFormModal';
import { EmptyState } from '../components/common/EmptyState';

export const ProductsView: React.FC = () => {
  const { products, warehouses } = useInventory();

  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [warehouseFilter, setWarehouseFilter] = useState('all');
  const [stockStatusFilter, setStockStatusFilter] = useState('all');

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const [transferProduct, setTransferProduct] = useState<Product | null>(null);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);

  const [adjustmentProduct, setAdjustmentProduct] = useState<Product | null>(null);
  const [isAdjustmentModalOpen, setIsAdjustmentModalOpen] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Filter Products
  const filteredProducts = products.filter((prod) => {
    const matchesSearch =
      prod.name.toLowerCase().includes(search.toLowerCase()) ||
      prod.sku.toLowerCase().includes(search.toLowerCase()) ||
      prod.category.toLowerCase().includes(search.toLowerCase());

    const matchesCategory = categoryFilter === 'all' || prod.category === categoryFilter;

    const totalStock = Object.values(prod.warehouseStock || {}).reduce((a, b) => a + b, 0);
    const stockStatus =
      totalStock === 0 ? 'Out of Stock' : totalStock <= prod.minReorderLevel ? 'Low Stock' : 'In Stock';

    const matchesStockStatus = stockStatusFilter === 'all' || stockStatus === stockStatusFilter;

    const matchesWarehouse =
      warehouseFilter === 'all' || (prod.warehouseStock[warehouseFilter] || 0) > 0;

    return matchesSearch && matchesCategory && matchesStockStatus && matchesWarehouse;
  });

  const totalPages = Math.ceil(filteredProducts.length / pageSize) || 1;
  const paginatedProducts = filteredProducts.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handleClearFilters = () => {
    setSearch('');
    setCategoryFilter('all');
    setWarehouseFilter('all');
    setStockStatusFilter('all');
    setCurrentPage(1);
  };

  return (
    <div className="space-y-5 pb-12 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Products & Inventory Catalog</h1>
          <p className="text-xs text-slate-500 mt-0.5">Manage products, SKUs and multi-warehouse stock availability</p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-sky-700 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-800 transition-colors shadow-xs"
        >
          <Plus className="h-4 w-4" />
          Create Product
        </button>
      </div>

      {/* Filter & Search Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-2xs">
        <div className="flex flex-wrap items-center gap-2.5 flex-1 min-w-[240px]">
          {/* Search Box */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search product name or SKU..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full rounded-md border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-3 text-xs text-slate-800 focus:border-sky-500 focus:bg-white focus:outline-none"
            />
          </div>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Category: All</option>
            <option value="Raw Materials">Raw Materials</option>
            <option value="Finished Goods">Finished Goods</option>
            <option value="Packaging">Packaging</option>
            <option value="Electrical">Electrical</option>
            <option value="Tools">Tools</option>
            <option value="Safety Equipment">Safety Equipment</option>
          </select>

          {/* Warehouse Filter */}
          <select
            value={warehouseFilter}
            onChange={(e) => {
              setWarehouseFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Warehouse: All Locations</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>

          {/* Stock Status Filter */}
          <select
            value={stockStatusFilter}
            onChange={(e) => {
              setStockStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none"
          >
            <option value="all">Stock Status: All</option>
            <option value="In Stock">In Stock</option>
            <option value="Low Stock">Low Stock</option>
            <option value="Out of Stock">Out of Stock</option>
          </select>
        </div>

        {(search || categoryFilter !== 'all' || warehouseFilter !== 'all' || stockStatusFilter !== 'all') && (
          <button
            onClick={handleClearFilters}
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-rose-700 underline"
          >
            <FilterX className="h-3.5 w-3.5" />
            Clear Filters
          </button>
        )}
      </div>

      {/* Product Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
        {filteredProducts.length === 0 ? (
          <EmptyState
            title="No Products Found"
            description="No SKUs match your search query or selected filter criteria."
            onClearFilters={handleClearFilters}
            actionLabel="Create Product SKU"
            onAction={() => setIsCreateModalOpen(true)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase font-bold text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3">SKU / Code</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Unit</th>
                  <th className="px-4 py-3 text-right">Main WH (WH-001)</th>
                  <th className="px-4 py-3 text-right">Prod Floor (WH-002)</th>
                  <th className="px-4 py-3 text-right">Total Stock</th>
                  <th className="px-4 py-3 text-right">Reorder Level</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {paginatedProducts.map((prod) => {
                  const totalStock = Object.values(prod.warehouseStock || {}).reduce((a, b) => a + b, 0);
                  const status =
                    totalStock === 0 ? 'Out of Stock' : totalStock <= prod.minReorderLevel ? 'Low Stock' : 'In Stock';
                  const mainWhStock = prod.warehouseStock['wh-001'] || 0;
                  const prodFloorStock = prod.warehouseStock['wh-002'] || 0;

                  return (
                    <tr
                      key={prod.id}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                      onClick={() => {
                        setSelectedProduct(prod);
                        setIsDetailModalOpen(true);
                      }}
                    >
                      <td className="px-4 py-3 font-semibold text-slate-900">{prod.name}</td>
                      <td className="px-4 py-3 font-mono font-medium text-slate-700">{prod.sku}</td>
                      <td className="px-4 py-3 text-slate-600">{prod.category}</td>
                      <td className="px-4 py-3 text-slate-500 font-mono">{prod.unit}</td>
                      <td className="px-4 py-3 text-right font-medium text-slate-800">{mainWhStock.toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-medium text-slate-800">{prodFloorStock.toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-bold text-slate-900">{totalStock.toLocaleString()}</td>
                      <td className="px-4 py-3 text-right text-slate-600">{prod.minReorderLevel}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={status} size="sm" />
                      </td>
                      <td
                        className="px-4 py-3 text-right space-x-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={() => {
                            setSelectedProduct(prod);
                            setIsDetailModalOpen(true);
                          }}
                          className="p-1 rounded text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                          title="View Product Details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => {
                            setTransferProduct(prod);
                            setIsTransferModalOpen(true);
                          }}
                          className="p-1 rounded text-amber-600 hover:bg-amber-50"
                          title="Transfer Stock"
                        >
                          <ArrowRightLeft className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => {
                            setAdjustmentProduct(prod);
                            setIsAdjustmentModalOpen(true);
                          }}
                          className="p-1 rounded text-purple-600 hover:bg-purple-50"
                          title="Adjust Stock"
                        >
                          <SlidersHorizontal className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        {filteredProducts.length > 0 && (
          <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3 bg-slate-50/50 text-xs">
            <span className="text-slate-500">
              Showing <span className="font-semibold text-slate-800">{(currentPage - 1) * pageSize + 1}</span> to{' '}
              <span className="font-semibold text-slate-800">
                {Math.min(currentPage * pageSize, filteredProducts.length)}
              </span>{' '}
              of <span className="font-semibold text-slate-800">{filteredProducts.length}</span> SKUs
            </span>

            <div className="flex items-center gap-1">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="px-2 font-semibold text-slate-800">
                Page {currentPage} of {totalPages}
              </span>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Feature Modals */}
      <ProductFormModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />

      <ProductDetailModal
        product={selectedProduct}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onOpenTransfer={(p) => {
          setTransferProduct(p);
          setIsTransferModalOpen(true);
        }}
        onOpenAdjustment={(p) => {
          setAdjustmentProduct(p);
          setIsAdjustmentModalOpen(true);
        }}
      />

      <TransferFormModal
        isOpen={isTransferModalOpen}
        onClose={() => setIsTransferModalOpen(false)}
        preselectedProduct={transferProduct}
      />

      <AdjustmentFormModal
        isOpen={isAdjustmentModalOpen}
        onClose={() => setIsAdjustmentModalOpen(false)}
        preselectedProduct={adjustmentProduct}
      />
    </div>
  );
};
