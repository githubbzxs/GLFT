import { useEffect, useState } from "react";
import { Block } from "baseui/block";
import { Button, SIZE } from "baseui/button";
import { Notification, KIND } from "baseui/notification";
import { LabelMedium, ParagraphSmall } from "baseui/typography";
import { useStyletron } from "baseui";
import api from "../api/client";
import { getErrorMessage } from "../api/errors";
import PageHeader from "../components/PageHeader";

type Metrics = {
  mid_price: number;
  inventory_btc: number;
  inventory_usd: number;
  unrealized_pnl: number;
  open_orders: number;
  spread: number;
  cancel_rate_per_min: number;
  order_rate_per_min: number;
};

const formatFixed = (value: number | undefined, digits: number): string => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "-";
  }
  return value.toFixed(digits);
};

type MetricTileProps = {
  title: string;
  value: string;
  accent?: boolean;
};

function MetricTile({ title, value, accent = false }: MetricTileProps) {
  const [css, theme] = useStyletron();

  return (
    <Block
      className={css({
        border: "1px solid #243452",
        borderRadius: theme.borders.radius500,
        backgroundColor: accent ? "rgba(28, 64, 128, 0.28)" : "rgba(13, 21, 34, 0.88)"
      })}
      paddingTop="scale500"
      paddingBottom="scale500"
      paddingLeft="scale600"
      paddingRight="scale600"
    >
      <ParagraphSmall marginTop="0" marginBottom="scale200" color="contentTertiary">
        {title}
      </ParagraphSmall>
      <LabelMedium marginTop="0" marginBottom="0">{value}</LabelMedium>
    </Block>
  );
}

export default function DashboardPage() {
  const [css] = useStyletron();
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const res = await api.get<Metrics>("/dashboard/metrics");
      setMetrics(res.data);
      setError("");
    } catch (loadError) {
      setError(getErrorMessage(loadError, "加载仪表盘数据失败"));
    }
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <Block>
      <PageHeader
        title="仪表盘"
        description="实时查看行情、库存与做市速率指标。"
        actions={
          <Button size={SIZE.compact} onClick={load}>
            刷新
          </Button>
        }
      />

      {error ? (
        <Notification kind={KIND.negative} closeable={false}>
          {error}
        </Notification>
      ) : null}

      <Block
        marginTop="scale700"
        className={css({
          display: "grid",
          gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          gap: "16px",
          "@media screen and (max-width: 1200px)": {
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))"
          },
          "@media screen and (max-width: 760px)": {
            gridTemplateColumns: "1fr"
          }
        })}
      >
        <MetricTile title="中间价" value={formatFixed(metrics?.mid_price, 2)} accent />
        <MetricTile title="库存 (BTC)" value={formatFixed(metrics?.inventory_btc, 4)} />
        <MetricTile title="库存 (USD)" value={formatFixed(metrics?.inventory_usd, 2)} />
        <MetricTile title="未实现盈亏" value={formatFixed(metrics?.unrealized_pnl, 2)} />
        <MetricTile title="挂单数量" value={String(metrics?.open_orders ?? "-")} />
        <MetricTile title="盘口价差" value={formatFixed(metrics?.spread, 2)} />
      </Block>

      <Block
        marginTop="scale800"
        className={css({
          borderRadius: "16px",
          padding: "16px",
          border: "1px solid #243452",
          backgroundColor: "rgba(13, 21, 34, 0.88)"
        })}
      >
        <LabelMedium marginTop="0" marginBottom="scale500">
          风控速览
        </LabelMedium>
        <Block
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: "16px",
            "@media screen and (max-width: 760px)": {
              gridTemplateColumns: "1fr"
            }
          })}
        >
          <MetricTile title="撤单率 / 分钟" value={formatFixed(metrics?.cancel_rate_per_min, 1)} />
          <MetricTile title="下单率 / 分钟" value={formatFixed(metrics?.order_rate_per_min, 1)} />
        </Block>
      </Block>
    </Block>
  );
}
