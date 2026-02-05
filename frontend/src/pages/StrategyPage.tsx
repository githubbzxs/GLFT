import { useEffect, useState } from "react";
import { Block } from "baseui/block";
import { Button, SIZE } from "baseui/button";
import { Checkbox } from "baseui/checkbox";
import { FormControl } from "baseui/form-control";
import { Input } from "baseui/input";
import { Notification, KIND } from "baseui/notification";
import { useStyletron } from "baseui";
import { toaster } from "baseui/toast";
import api from "../api/client";
import { getErrorMessage } from "../api/errors";
import PageHeader from "../components/PageHeader";

type Params = {
  gamma: number;
  sigma: number;
  A: number;
  k: number;
  time_horizon_seconds: number;
  inventory_cap_usd: number;
  order_cap_usd: number;
  leverage_limit: number;
  auto_tuning_enabled: boolean;
};

type NumericKey = Exclude<keyof Params, "auto_tuning_enabled">;

const numericFields: Array<{ key: NumericKey; label: string; description?: string }> = [
  { key: "gamma", label: "风险厌恶系数 gamma" },
  { key: "sigma", label: "波动率 sigma" },
  { key: "A", label: "到达强度 A" },
  { key: "k", label: "盘口斜率 k" },
  { key: "time_horizon_seconds", label: "时间窗口（秒）" },
  { key: "inventory_cap_usd", label: "库存上限（USD）" },
  { key: "order_cap_usd", label: "单笔上限（USD）" },
  { key: "leverage_limit", label: "杠杆上限" }
];

const parseNumber = (value: string, fallback: number): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export default function StrategyPage() {
  const [css, theme] = useStyletron();
  const [params, setParams] = useState<Params | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<Params>("/strategy/params");
      setParams(res.data);
      setError("");
    } catch (loadError) {
      setError(getErrorMessage(loadError, "加载策略参数失败"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const updateNumber = (key: NumericKey, value: string) => {
    setParams((prev) => {
      if (!prev) {
        return prev;
      }
      return { ...prev, [key]: parseNumber(value, prev[key]) };
    });
  };

  const save = async () => {
    if (!params) {
      return;
    }

    setSaving(true);
    try {
      const response = await api.post<Params>("/strategy/params", params);
      setParams(response.data);
      setError("");
      toaster.positive("策略参数已更新");
    } catch (saveError) {
      setError(getErrorMessage(saveError, "保存策略参数失败"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Block>
      <PageHeader
        title="策略参数"
        description="管理 GLFT 模型参数与做市约束。"
        actions={
          <Block
            display="flex"
            className={css({
              gap: "10px"
            })}
          >
            <Button size={SIZE.compact} kind="tertiary" isLoading={loading} onClick={load}>
              刷新
            </Button>
            <Button size={SIZE.compact} isLoading={saving} onClick={save}>
              保存参数
            </Button>
          </Block>
        }
      />

      {error ? (
        <Notification kind={KIND.negative} closeable={false}>
          {error}
        </Notification>
      ) : null}

      {!params && loading ? (
        <Notification kind={KIND.info} closeable={false}>
          正在加载策略参数...
        </Notification>
      ) : null}

      {params ? (
        <Block
          marginTop="scale700"
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: "16px",
            "@media screen and (max-width: 860px)": {
              gridTemplateColumns: "1fr"
            }
          })}
        >
          {numericFields.map((field) => (
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
              <FormControl label={field.label} caption={field.description}>
                <Input
                  type="number"
                  value={String(params[field.key])}
                  onChange={(event) => updateNumber(field.key, event.currentTarget.value)}
                />
              </FormControl>
            </Block>
          ))}

          <Block
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
            <Checkbox
              checked={params.auto_tuning_enabled}
              onChange={(event) =>
                setParams((prev) =>
                  prev
                    ? {
                        ...prev,
                        auto_tuning_enabled: event.currentTarget.checked
                      }
                    : prev
                )
              }
            >
              启用自动调参
            </Checkbox>
          </Block>
        </Block>
      ) : null}
    </Block>
  );
}
