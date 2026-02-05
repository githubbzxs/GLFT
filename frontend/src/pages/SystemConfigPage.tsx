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

type Config = {
  grvt_env: string;
  grvt_symbol: string;
  quote_interval_ms: number;
  order_duration_secs: number;
  calibration_window_days: number;
  calibration_timeframe: string;
  calibration_update_time: string;
  calibration_trade_sample: number;
  log_retention_days: number;
  alert_email_to: string;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_password_set: boolean;
  smtp_tls: boolean;
};

type NumericConfigKey =
  | "quote_interval_ms"
  | "order_duration_secs"
  | "calibration_window_days"
  | "calibration_trade_sample"
  | "log_retention_days"
  | "smtp_port";

const parseNumber = (value: string, fallback: number) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export default function SystemConfigPage() {
  const [css, theme] = useStyletron();
  const [config, setConfig] = useState<Config | null>(null);
  const [smtpPassword, setSmtpPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<Config>("/config");
      setConfig(res.data);
      setError("");
    } catch (loadError) {
      setError(getErrorMessage(loadError, "加载系统配置失败"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const updateNumberConfig = (key: NumericConfigKey, value: string) => {
    setConfig((prev) => {
      if (!prev) {
        return prev;
      }
      return { ...prev, [key]: parseNumber(value, prev[key]) };
    });
  };

  const save = async () => {
    if (!config) {
      return;
    }

    setSaving(true);
    try {
      const payload = {
        ...config,
        smtp_password: smtpPassword
      };
      const res = await api.post<Config>("/config", payload);
      setConfig(res.data);
      setSmtpPassword("");
      setError("");
      toaster.positive("系统配置已保存");
    } catch (saveError) {
      setError(getErrorMessage(saveError, "保存系统配置失败"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Block>
      <PageHeader
        title="系统配置"
        description="配置交易环境、回推任务与告警邮件通道。"
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
            <Button size={SIZE.compact} isLoading={saving} onClick={save} disabled={!config}>
              保存配置
            </Button>
          </Block>
        }
      />

      {error ? (
        <Notification kind={KIND.negative} closeable={false}>
          {error}
        </Notification>
      ) : null}

      {!config && loading ? (
        <Notification kind={KIND.info} closeable={false}>
          正在加载配置...
        </Notification>
      ) : null}

      {config ? (
        <>
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
              className={css({
                display: "grid",
                gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                gap: "16px",
                "@media screen and (max-width: 900px)": {
                  gridTemplateColumns: "1fr"
                }
              })}
            >
              <FormControl label="GRVT 环境">
                <Input
                  value={config.grvt_env}
                  onChange={(event) =>
                    setConfig((prev) => (prev ? { ...prev, grvt_env: event.currentTarget.value } : prev))
                  }
                  placeholder="prod / testnet / staging / dev"
                />
              </FormControl>
              <FormControl label="交易标的">
                <Input
                  value={config.grvt_symbol}
                  onChange={(event) =>
                    setConfig((prev) =>
                      prev ? { ...prev, grvt_symbol: event.currentTarget.value } : prev
                    )
                  }
                />
              </FormControl>
              <FormControl label="报价间隔（ms）">
                <Input
                  type="number"
                  value={String(config.quote_interval_ms)}
                  onChange={(event) => updateNumberConfig("quote_interval_ms", event.currentTarget.value)}
                />
              </FormControl>
              <FormControl label="订单有效期（秒）">
                <Input
                  type="number"
                  value={String(config.order_duration_secs)}
                  onChange={(event) => updateNumberConfig("order_duration_secs", event.currentTarget.value)}
                />
              </FormControl>
              <FormControl label="回推窗口（天）">
                <Input
                  type="number"
                  value={String(config.calibration_window_days)}
                  onChange={(event) =>
                    updateNumberConfig("calibration_window_days", event.currentTarget.value)
                  }
                />
              </FormControl>
              <FormControl label="回推周期">
                <Input
                  value={config.calibration_timeframe}
                  onChange={(event) =>
                    setConfig((prev) =>
                      prev ? { ...prev, calibration_timeframe: event.currentTarget.value } : prev
                    )
                  }
                />
              </FormControl>
              <FormControl label="回推执行时间（HH:MM）">
                <Input
                  value={config.calibration_update_time}
                  onChange={(event) =>
                    setConfig((prev) =>
                      prev ? { ...prev, calibration_update_time: event.currentTarget.value } : prev
                    )
                  }
                />
              </FormControl>
              <FormControl label="回推样本数">
                <Input
                  type="number"
                  value={String(config.calibration_trade_sample)}
                  onChange={(event) =>
                    updateNumberConfig("calibration_trade_sample", event.currentTarget.value)
                  }
                />
              </FormControl>
              <FormControl label="日志留存（天）">
                <Input
                  type="number"
                  value={String(config.log_retention_days)}
                  onChange={(event) => updateNumberConfig("log_retention_days", event.currentTarget.value)}
                />
              </FormControl>
            </Block>
          </Block>

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
              className={css({
                display: "grid",
                gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                gap: "16px",
                "@media screen and (max-width: 900px)": {
                  gridTemplateColumns: "1fr"
                }
              })}
            >
              <FormControl label="告警邮箱">
                <Input
                  value={config.alert_email_to}
                  onChange={(event) =>
                    setConfig((prev) =>
                      prev ? { ...prev, alert_email_to: event.currentTarget.value } : prev
                    )
                  }
                />
              </FormControl>
              <FormControl label="SMTP Host">
                <Input
                  value={config.smtp_host}
                  onChange={(event) =>
                    setConfig((prev) =>
                      prev ? { ...prev, smtp_host: event.currentTarget.value } : prev
                    )
                  }
                />
              </FormControl>
              <FormControl label="SMTP 端口">
                <Input
                  type="number"
                  value={String(config.smtp_port)}
                  onChange={(event) => updateNumberConfig("smtp_port", event.currentTarget.value)}
                />
              </FormControl>
              <FormControl label="SMTP 用户">
                <Input
                  value={config.smtp_user}
                  onChange={(event) =>
                    setConfig((prev) =>
                      prev ? { ...prev, smtp_user: event.currentTarget.value } : prev
                    )
                  }
                />
              </FormControl>
              <FormControl
                label={config.smtp_password_set ? "SMTP 密码（已设置）" : "SMTP 密码"}
                caption="留空表示不更新密码"
              >
                <Input
                  type="password"
                  value={smtpPassword}
                  onChange={(event) => setSmtpPassword(event.currentTarget.value)}
                />
              </FormControl>
              <FormControl label="SMTP TLS">
                <Checkbox
                  checked={config.smtp_tls}
                  onChange={(event) =>
                    setConfig((prev) =>
                      prev ? { ...prev, smtp_tls: event.currentTarget.checked } : prev
                    )
                  }
                >
                  启用 TLS
                </Checkbox>
              </FormControl>
            </Block>
          </Block>
        </>
      ) : null}
    </Block>
  );
}
