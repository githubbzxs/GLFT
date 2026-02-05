import { useEffect, useState } from "react";
import { Block } from "baseui/block";
import { Button, SIZE } from "baseui/button";
import { Notification, KIND } from "baseui/notification";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { TableBuilder, TableBuilderColumn } from "baseui/table-semantic";
import { Tab, Tabs } from "baseui/tabs-motion";
import { ParagraphSmall } from "baseui/typography";
import api from "../api/client";
import { getErrorMessage } from "../api/errors";
import PageHeader from "../components/PageHeader";

type Order = {
  order_id: string;
  symbol: string;
  side: string;
  price: number;
  size: number;
  status: string;
};

type Trade = {
  trade_id: string;
  symbol: string;
  side: string;
  price: number;
  size: number;
  fee: number;
  realized_pnl: number;
};

type Position = {
  symbol: string;
  size: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
};

type TabKey = "orders" | "trades" | "positions";

const toFixedSafe = (value: number, digits = 2) => {
  if (!Number.isFinite(value)) {
    return "-";
  }
  return value.toFixed(digits);
};

const statusKind = (status: string) => {
  const normalized = status.toLowerCase();
  if (normalized.includes("fill")) {
    return TAG_KIND.positive;
  }
  if (normalized.includes("cancel")) {
    return TAG_KIND.warning;
  }
  if (normalized.includes("reject")) {
    return TAG_KIND.negative;
  }
  return TAG_KIND.neutral;
};

const sideKind = (side: string) =>
  side.toLowerCase() === "buy" ? TAG_KIND.positive : TAG_KIND.accent;

export default function OrdersPage() {
  const [activeKey, setActiveKey] = useState<TabKey>("orders");
  const [orders, setOrders] = useState<Order[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [orderRes, tradeRes, positionRes] = await Promise.all([
        api.get<Order[]>("/orders"),
        api.get<Trade[]>("/trades"),
        api.get<Position[]>("/positions")
      ]);
      setOrders(orderRes.data);
      setTrades(tradeRes.data);
      setPositions(positionRes.data);
      setError("");
    } catch (loadError) {
      setError(getErrorMessage(loadError, "加载订单与成交数据失败"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <Block>
      <PageHeader
        title="订单 / 成交 / 持仓"
        description="统一查看交易执行历史与当前仓位。"
        actions={
          <Button size={SIZE.compact} isLoading={loading} onClick={load}>
            刷新
          </Button>
        }
      />

      {error ? (
        <Notification kind={KIND.negative} closeable={false}>
          {error}
        </Notification>
      ) : null}

      <Block marginTop="scale700">
        <Tabs
          activateOnFocus
          activeKey={activeKey}
          onChange={({ activeKey: nextActiveKey }) => setActiveKey(nextActiveKey as TabKey)}
        >
          <Tab title="订单">
            {orders.length === 0 ? (
              <ParagraphSmall color="contentSecondary">暂无订单数据</ParagraphSmall>
            ) : (
              <TableBuilder data={orders}>
                <TableBuilderColumn header="订单号">
                  {(row: Order) => row.order_id}
                </TableBuilderColumn>
                <TableBuilderColumn header="标的">
                  {(row: Order) => row.symbol}
                </TableBuilderColumn>
                <TableBuilderColumn header="方向">
                  {(row: Order) => (
                    <Tag closeable={false} kind={sideKind(row.side)}>
                      {row.side}
                    </Tag>
                  )}
                </TableBuilderColumn>
                <TableBuilderColumn header="价格">
                  {(row: Order) => toFixedSafe(row.price)}
                </TableBuilderColumn>
                <TableBuilderColumn header="数量">
                  {(row: Order) => String(row.size)}
                </TableBuilderColumn>
                <TableBuilderColumn header="状态">
                  {(row: Order) => (
                    <Tag closeable={false} kind={statusKind(row.status)}>
                      {row.status}
                    </Tag>
                  )}
                </TableBuilderColumn>
              </TableBuilder>
            )}
          </Tab>

          <Tab title="成交">
            {trades.length === 0 ? (
              <ParagraphSmall color="contentSecondary">暂无成交数据</ParagraphSmall>
            ) : (
              <TableBuilder data={trades}>
                <TableBuilderColumn header="成交号">
                  {(row: Trade) => row.trade_id}
                </TableBuilderColumn>
                <TableBuilderColumn header="标的">
                  {(row: Trade) => row.symbol}
                </TableBuilderColumn>
                <TableBuilderColumn header="方向">
                  {(row: Trade) => (
                    <Tag closeable={false} kind={sideKind(row.side)}>
                      {row.side}
                    </Tag>
                  )}
                </TableBuilderColumn>
                <TableBuilderColumn header="价格">
                  {(row: Trade) => toFixedSafe(row.price)}
                </TableBuilderColumn>
                <TableBuilderColumn header="数量">
                  {(row: Trade) => String(row.size)}
                </TableBuilderColumn>
                <TableBuilderColumn header="手续费">
                  {(row: Trade) => toFixedSafe(row.fee, 6)}
                </TableBuilderColumn>
                <TableBuilderColumn header="已实现盈亏">
                  {(row: Trade) => toFixedSafe(row.realized_pnl)}
                </TableBuilderColumn>
              </TableBuilder>
            )}
          </Tab>

          <Tab title="持仓">
            {positions.length === 0 ? (
              <ParagraphSmall color="contentSecondary">暂无持仓数据</ParagraphSmall>
            ) : (
              <TableBuilder data={positions}>
                <TableBuilderColumn header="标的">
                  {(row: Position) => row.symbol}
                </TableBuilderColumn>
                <TableBuilderColumn header="仓位">
                  {(row: Position) => String(row.size)}
                </TableBuilderColumn>
                <TableBuilderColumn header="成本价">
                  {(row: Position) => toFixedSafe(row.entry_price)}
                </TableBuilderColumn>
                <TableBuilderColumn header="标记价">
                  {(row: Position) => toFixedSafe(row.mark_price)}
                </TableBuilderColumn>
                <TableBuilderColumn header="未实现盈亏">
                  {(row: Position) => toFixedSafe(row.unrealized_pnl)}
                </TableBuilderColumn>
              </TableBuilder>
            )}
          </Tab>
        </Tabs>
      </Block>
    </Block>
  );
}
