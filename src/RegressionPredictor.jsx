import React, { useState } from 'react';
import { Calculator, TrendingUp } from 'lucide-react';

export default function RegressionPredictor({ model }) {
  const [price, setPrice] = useState(200000);
  const [authentic, setAuthentic] = useState(1);
  const [delivery, setDelivery] = useState(3);

  const lnSales = model.intercept
    + model.beta_price * price
    + model.beta_authentic * authentic
    + model.beta_delivery * delivery
    + model.beta_price_auth * price * authentic;
  const predictedSales = Math.max(0, Math.round(Math.exp(lnSales) - 1));

  return (
    <div className="rounded-2xl border border-purple-200 bg-gradient-to-r from-purple-50 to-violet-50 p-5 shadow-sm">
      <h3 className="text-xs font-bold font-mono uppercase text-purple-800 mb-3 flex items-center gap-1.5">
        <Calculator className="w-3.5 h-3.5" /> Máy tính dự báo — ASG2 Q2
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div>
          <label className="text-[10px] font-semibold text-gray-500 uppercase block mb-1">Giá (VNĐ)</label>
          <input type="number" value={price} onChange={e => setPrice(Number(e.target.value))}
            className="w-full px-3 py-2 rounded-lg border border-purple-200 text-xs font-mono bg-white focus:ring-2 focus:ring-purple-400 focus:outline-none" />
        </div>
        <div>
          <label className="text-[10px] font-semibold text-gray-500 uppercase block mb-1">Chính hãng</label>
          <select value={authentic} onChange={e => setAuthentic(Number(e.target.value))}
            className="w-full px-3 py-2 rounded-lg border border-purple-200 text-xs font-mono bg-white focus:ring-2 focus:ring-purple-400 focus:outline-none">
            <option value={1}>Có (Official Store)</option>
            <option value={0}>Không (Regular)</option>
          </select>
        </div>
        <div>
          <label className="text-[10px] font-semibold text-gray-500 uppercase block mb-1">Giao hàng (ngày)</label>
          <input type="number" value={delivery} onChange={e => setDelivery(Number(e.target.value))} min={1} max={7}
            className="w-full px-3 py-2 rounded-lg border border-purple-200 text-xs font-mono bg-white focus:ring-2 focus:ring-purple-400 focus:outline-none" />
        </div>
        <div className="flex flex-col justify-center items-center bg-white rounded-lg border border-purple-200 p-3">
          <span className="text-[10px] font-semibold text-gray-500 uppercase">Dự báo sold_count</span>
          <span className="text-2xl font-bold font-mono text-purple-700">{predictedSales.toLocaleString()}</span>
          <span className="text-[10px] text-gray-400">ln(sold+1) = {lnSales.toFixed(4)}</span>
        </div>
      </div>
      <div className="flex items-center gap-2 text-[10px] text-purple-700 bg-purple-100 border border-purple-300 rounded-lg px-3 py-2">
        <TrendingUp className="w-3.5 h-3.5 flex-shrink-0" />
        <span><strong>Hướng dẫn:</strong> Thay đổi giá, chính hãng, giao hàng để xem tác động đến dự báo. Official Store (chính hãng) bán gấp ~2.2 lần regular cùng điều kiện.</span>
      </div>
    </div>
  );
}
