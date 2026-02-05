import { useEffect, useState } from "react";
import { Block } from "baseui/block";
import { Button, SIZE } from "baseui/button";
import { FormControl } from "baseui/form-control";
import { Input } from "baseui/input";
import { Notification, KIND } from "baseui/notification";
import { Textarea } from "baseui/textarea";
import { useStyletron } from "baseui";
import { toaster } from "baseui/toast";
import api from "../api/client";
import { getErrorMessage } from "../api/errors";
import PageHeader from "../components/PageHeader";

type ApiKeyInfo = {
  sub_account_id: string;
  ip_whitelist: string;
};

export default function ApiKeysPage() {
  const [css, theme] = useStyletron();
  const [apiKey, setApiKey] = useState("");
  const [privateKey, setPrivateKey] = useState("");
  const [subAccountId, setSubAccountId] = useState("");
  const [ipWhitelist, setIpWhitelist] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<ApiKeyInfo>("/keys");
      setSubAccountId(res.data.sub_account_id);
      setIpWhitelist(res.data.ip_whitelist || "");
      setError("");
    } catch (loadError) {
      setError(getErrorMessage(loadError, "尚未配置 API Key"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await api.post("/keys", {
        api_key: apiKey,
        private_key: privateKey,
        sub_account_id: subAccountId.trim(),
        ip_whitelist: ipWhitelist.trim()
      });
      setApiKey("");
      setPrivateKey("");
      setError("");
      toaster.positive("密钥已保存（服务端加密）");
      await load();
    } catch (saveError) {
      setError(getErrorMessage(saveError, "保存 API Key 失败"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Block>
      <PageHeader
        title="API Key 管理"
        description="配置 GRVT API 凭据，密钥仅在输入时可见。"
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
              保存密钥
            </Button>
          </Block>
        }
      />

      {error ? (
        <Notification kind={KIND.warning} closeable={false}>
          {error}
        </Notification>
      ) : null}

      <Block
        marginTop="scale700"
        className={css({
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          gap: "16px",
          "@media screen and (max-width: 900px)": {
            gridTemplateColumns: "1fr"
          }
        })}
      >
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
          <FormControl label="GRVT API Key">
            <Input
              value={apiKey}
              type="password"
              onChange={(event) => setApiKey(event.currentTarget.value)}
              placeholder="请输入 API Key"
            />
          </FormControl>
          <FormControl label="GRVT Private Key">
            <Textarea
              value={privateKey}
              onChange={(event) => setPrivateKey(event.currentTarget.value)}
              placeholder="请输入 Private Key"
            />
          </FormControl>
        </Block>

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
          <FormControl label="Sub Account ID">
            <Input
              value={subAccountId}
              onChange={(event) => setSubAccountId(event.currentTarget.value)}
              placeholder="请输入子账户 ID"
            />
          </FormControl>
          <FormControl label="IP 白名单（逗号分隔）">
            <Textarea
              value={ipWhitelist}
              onChange={(event) => setIpWhitelist(event.currentTarget.value)}
              placeholder="例如 1.1.1.1,2.2.2.2"
            />
          </FormControl>
        </Block>
      </Block>
    </Block>
  );
}
