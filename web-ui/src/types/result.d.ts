// Based on the data structure from web_server.py and scraper.py

export interface ProductInfo {
  "商品标题": string;
  "当前售价": string;
  "商品原价"?: string;
  "“想要”人数"?: string | number;
  "商品标签"?: string[];
  "发货地区"?: string;
  "卖家昵称"?: string;
  "商品链接": string;
  "发布时间"?: string;
  "商品ID": string;
  "商品图片列表"?: string[];
  "商品主图链接"?: string;
  "浏览量"?: string | number;
}

export interface SellerInfo {
  "卖家昵称"?: string;
  "卖家头像链接"?: string;
  "卖家个性签名"?: string;
  "卖家在售/已售商品数"?: string;
  "卖家收到的评价总数"?: string;
  "卖家信用等级"?: string;
  "买家信用等级"?: string;
  "卖家芝麻信用"?: string;
  "卖家注册时长"?: string;
  "作为卖家的好评数"?: string;
  "作为卖家的好评率"?: string;
  "作为买家的好评数"?: string;
  "作为买家的好评率"?: string;
  "卖家发布的商品列表"?: any[]; // Define more strictly if needed
  "卖家收到的评价列表"?: any[]; // Define more strictly if needed
}

export interface AiAnalysis {
  is_recommended: boolean;
  reason: string;
  analysis_source?: 'ai' | 'keyword';
  keyword_hit_count?: number;
  value_score?: number;
  value_summary?: string;
  prompt_version?: string;
  risk_tags?: string[];
  criteria_analysis?: Record<string, any>;
  matched_keywords?: string[];
  error?: string;
}

export interface PriceInsight {
  observation_count: number;
  current_price?: number | null;
  avg_price?: number | null;
  median_price?: number | null;
  min_price?: number | null;
  max_price?: number | null;
  market_avg_price?: number | null;
  market_median_price?: number | null;
  market_sample_count?: number;
  market_raw_sample_count?: number;
  market_p25_price?: number | null;
  market_p35_price?: number | null;
  market_p50_price?: number | null;
  market_p75_price?: number | null;
  market_valuation_eligible?: boolean;
  market_excluded_sample_count?: number;
  market_valuation_window_days?: number | null;
  market_model_key?: string | null;
  price_change_amount?: number | null;
  price_change_percent?: number | null;
  deal_score?: number | null;
  deal_label?: string;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
}

export interface OpportunityAssessment {
  score: number | null;
  label: string;
  confidence: 'high' | 'medium' | 'low';
  suggested_listing_price: number | null;
  recommended_max_purchase_price: number | null;
  expected_profit: number | null;
  expected_margin: number | null;
  market_sample_count: number;
  price_discount_percent: number | null;
  components: Record<string, number>;
  reasons: string[];
  risk_notes: string[];
}

export interface PricingAssessment {
  status: 'priority_buy' | 'negotiate' | 'not_recommended' | 'insufficient_data' | 'low_confidence' | 'risk_blocked';
  label: string;
  can_buy: boolean;
  confidence: 'high' | 'medium' | 'low';
  is_gpu: boolean;
  market_sample_count: number;
  market_raw_sample_count: number;
  market_excluded_sample_count: number;
  min_samples_for_quote: number;
  price_band: { p25: number | null; p35: number | null; p50: number | null; p75: number | null };
  quick_sale_price: number | null;
  conservative_resale_price: number | null;
  suggested_listing_price: number | null;
  recommended_max_purchase_price: number | null;
  expected_profit: number | null;
  expected_margin: number | null;
  state_adjustment_rate: number;
  state_adjustment_signals: string[];
  cost_breakdown: Record<string, number>;
  current_price: number | null;
  gap_to_max_purchase_price: number | null;
  reasons: string[];
  risk_notes: string[];
}

export interface ProfitEstimate {
  purchase_price: number;
  resale_price: number;
  platform_fee: number;
  shipping_cost: number;
  other_cost: number;
  profit?: number;
  margin?: number;
  updated_at?: string;
}

export type InventoryStatus =
  | 'discovered'
  | 'contacting'
  | 'purchased'
  | 'listed'
  | 'sold'
  | 'skipped'

export interface InventoryRecord {
  status: InventoryStatus;
  actual_purchase_price: number | null;
  actual_sale_price: number | null;
  actual_platform_fee: number;
  actual_shipping_cost: number;
  actual_other_cost: number;
  actual_profit?: number | null;
  actual_margin?: number | null;
  notes: string;
  purchased_at?: string | null;
  listed_at?: string | null;
  sold_at?: string | null;
  updated_at?: string;
}

export interface ResultInsights {
  market_summary: {
    sample_count: number;
    avg_price: number | null;
    median_price: number | null;
    min_price: number | null;
    max_price: number | null;
    snapshot_time?: string | null;
  };
  history_summary: {
    unique_items: number;
    sample_count: number;
    avg_price: number | null;
    median_price: number | null;
    min_price: number | null;
    max_price: number | null;
  };
  daily_trend: Array<{
    day: string;
    sample_count: number;
    avg_price: number | null;
    median_price: number | null;
    min_price: number | null;
    max_price: number | null;
  }>;
  latest_snapshot_at?: string | null;
  business_summary?: BusinessSummary;
}

export interface BusinessSummary {
  tracked_items: number;
  status_counts: Record<string, number>;
  owned_items: number;
  open_inventory_items: number;
  capital_deployed: number;
  open_inventory_cost: number;
  sold_items: number;
  settled_sales: number;
  realized_profit: number;
  realized_roi: number | null;
  average_turnover_days: number | null;
  turnover_sample_count: number;
  incomplete_sold_items: number;
  model_performance: Array<{
    model_key: string;
    sold_items: number;
    settled_sales: number;
    realized_profit: number;
    roi: number | null;
    average_turnover_days: number | null;
  }>;
}

export interface ResultItem {
  "爬取时间": string;
  "搜索关键字": string;
  "任务名称": string;
  "商品信息": ProductInfo;
  "卖家信息": SellerInfo;
  ai_analysis: AiAnalysis;
  price_insight?: PriceInsight;
  profit_estimate?: ProfitEstimate;
  inventory_record?: InventoryRecord;
  opportunity_assessment?: OpportunityAssessment;
  pricing_assessment?: PricingAssessment;
  _status?: 'active' | 'hidden' | 'expired';
  _effective_hidden?: boolean;
  _hidden_reason?: 'manual' | 'rule' | 'expired' | null;
  _matched_blacklist_keywords?: string[];
}
