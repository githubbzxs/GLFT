import { useEffect, useState } from "react";
import { Block } from "baseui/block";
import { Button, SIZE } from "baseui/button";
import { FormControl } from "baseui/form-control";
import { Input } from "baseui/input";
import { Notification, KIND } from "baseui/notification";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { LabelMedium, ParagraphSmall } from "baseui/typography";
import { useStyletron } from "baseui";
import { toaster } from "baseui/toast";
import api from "../api/client";
import { getErrorMessage } from "../api/errors";
import PageHeader from "../components/PageHeader";

type RiskStatus = {
  is_trading: boolean;
  last_event?: string;
  cancel_rate_per_min: number;
  order_rate_per_min: number;
};

type Limits = {
  max_inventory_usd: number;
  max_order_usd: number;
  max_leverage: number;
  max_cancel_rate_per_min: number;
  max_order_rate_per_min: number;
};

type LimitKey = keyof Limits;

const parseNumber = (value: string, fallback: number) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const fields: Array<{ key: LimitKey; label: string }> = [
  { key: "max_inventory_usd", label: "最大库存（USD）" },
  { key: "max_order_usd", label: "单笔上限（USD）" },
  { key: "max_leverage", label: "最大杠杆" },
  { key: "max_cancel_rate_per_min", label: "最大撤单率 / 分钟" },
  { key: "max_order_rate_per_min", label: "最大下单率 / 分钟" }
];

export default function RiskPage() {
  const [css, theme] = useStyletron();
  const [status, setStatus] = useState<RiskStatus | null>(null);
  const [limits, setLimits] = useState<Limits>({
    max_inventory_usd: 100,
    max_order_usd: 20,
    max_leverage: 50,
    max_cancel_rate_per_min: 0.85,
    max_order_rate_per_min: 120
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<RiskStatus>("/risk/status");
      setStatus(res.data);
      setError("");
    } catch (loadError) {
      setError(getErrorMessage(loadError, "加载风控状态失败"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, []);

  const updateLimits = async () => {
    try {
      await api.post("/risk/limits", limits);
      toaster.positive("风控阈值已更新");
      setError("");
    } catch (updateError) {
      setError(getErrorMessage(updateError, "更新风控阈值失败"));
    }
  };

  const startEngine = async () => {
    try {
      await api.post("/engine/start");
      toaster.positive("引擎已启动");
      await load();
    } catch (startError) {
      setError(getErrorMessage(startError, "启动引擎失败"));
    }
  };

  const stopEngine = async () => {
    try {
      await api.post("/engine/stop");
      toaster.warning("引擎已停止");
      await load();
    } catch (stopError) {
      setError(getErrorMessage(stopError, "停止引擎失败"));
    }
  };

  return (
    <Block>
      <PageHeader
        title="风控执行"
        description="管理引擎启停与实时风控阈值。"
        actions={
          <Block
            display="flex"
            flexWrap
            className={css({
              gap: "10px"
            })}
          >
            <Button size={SIZE.compact} kind="secondary" onClick={startEngine}>
              启动引擎
            </Button>
            <Button size={SIZE.compact} kind="tertiary" onClick={stopEngine}>
              停止引擎
            </Button>
            <Button size={SIZE.compact} kind="primary" isLoading={loading} onClick={load}>
              刷新状态
            </Button>
          </Block>
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
          border: "1px solid #243452",
          borderRadius: theme.borders.radius500,
          backgroundColor: "rgba(13, 21, 34, 0.88)"
        })}
        paddingTop="scale600"
        paddingBottom="scale600"
        paddingLeft="scale600"
        paddingRight="scale600"
      >
        <Block
          display="flex"
          alignItems="center"
          marginBottom="scale400"
          className={css({
            gap: "10px"
          })}
        >
          <LabelMedium marginTop="0" marginBottom="0">引擎状态</LabelMedium>
          <Tag
            closeable={false}
            kind={status?.is_trading ? TAG_KIND.positive : TAG_KIND.warning}
          >
            {status?.is_trading ? "运行中" : "已停止"}
          </Tag>
        </Block>
        <ParagraphSmall marginTop="0" marginBottom="scale200" color="contentSecondary">
          最近事件：{status?.last_event || "暂无"}
        </ParagraphSmall>
        <ParagraphSmall marginTop="0" marginBottom="scale200" color="contentSecondary">
          撤单率 / 分钟：{status ? status.cancel_rate_per_min.toFixed(2) : "-"}
        </ParagraphSmall>
        <ParagraphSmall marginTop="0" marginBottom="0" color="contentSecondary">
          下单率 / 分钟：{status ? status.order_rate_per_min.toFixed(2) : "-"}
        </ParagraphSmall>
      </Block>

      <Block
        marginTop="scale700"
        className={css({
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          gap: "16px",
          "@media screen and (max-width: 820px)": {
            gridTemplateColumns: "1fr"
          }
        })}
      >
        {fields.map((field) => (
          <Block
            key={field.key}
            className={css({
              border: "1px solid #243452",
              borderRadius: theme.borders.radius500,
              backgroundColor: "rgba(13, 21, 34, 0.88)"
            })}
            paddingTop="scale600"
            paddingBottom="scale600"
            paddingLeft="scale600"
            paddingRight="scale600"
          >
            <FormControl label={field.label}>
              <Input
                type="number"
                value={String(limits[field.key])}
                onChange={(event) =>
                  setLimits((prev) => ({
                    ...prev,
                    [field.key]: parseNumber(event.currentTarget.value, prev[field.key])
                  }))
                }
              />
            </FormControl>
          </Block>
        ))}
      </Block>

      <Block marginTop="scale700">
        <Button onClick={updateLimits}>保存风控阈值</Button>
      </Block>
    </Block>
  );
}
