import { useEffect, useState } from "react";
import { Block } from "baseui/block";
import { Button, SIZE } from "baseui/button";
import { Notification, KIND } from "baseui/notification";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { TableBuilder, TableBuilderColumn } from "baseui/table-semantic";
import { ParagraphSmall } from "baseui/typography";
import { toaster } from "baseui/toast";
import api from "../api/client";
import { getErrorMessage } from "../api/errors";
import PageHeader from "../components/PageHeader";

type Alert = {
  id: number;
  level: string;
  message: string;
  is_read: boolean;
};

const levelTagKind = (level: string) => {
  const normalized = level.toLowerCase();
  if (normalized.includes("critical") || normalized.includes("error")) {
    return TAG_KIND.negative;
  }
  if (normalized.includes("warn")) {
    return TAG_KIND.warning;
  }
  return TAG_KIND.accent;
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get<Alert[]>("/alerts");
      setAlerts(res.data);
      setError("");
    } catch (loadError) {
      setError(getErrorMessage(loadError, "加载告警失败"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const markRead = async (id: number) => {
    try {
      await api.post(`/alerts/${id}/read`);
      toaster.info("已标记为已读");
      await load();
    } catch (markError) {
      setError(getErrorMessage(markError, "更新告警状态失败"));
    }
  };

  return (
    <Block>
      <PageHeader
        title="告警中心"
        description="跟踪系统告警并处理未读项。"
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
        {alerts.length === 0 ? (
          <ParagraphSmall color="contentSecondary">当前没有告警记录</ParagraphSmall>
        ) : (
          <TableBuilder data={alerts}>
            <TableBuilderColumn header="级别">
              {(row: Alert) => (
                <Tag closeable={false} kind={levelTagKind(row.level)}>
                  {row.level}
                </Tag>
              )}
            </TableBuilderColumn>
            <TableBuilderColumn header="内容">
              {(row: Alert) => row.message}
            </TableBuilderColumn>
            <TableBuilderColumn header="状态">
              {(row: Alert) => (
                <Tag
                  closeable={false}
                  kind={row.is_read ? TAG_KIND.neutral : TAG_KIND.warning}
                >
                  {row.is_read ? "已读" : "未读"}
                </Tag>
              )}
            </TableBuilderColumn>
            <TableBuilderColumn header="操作">
              {(row: Alert) =>
                row.is_read ? (
                  "-"
                ) : (
                  <Button
                    size={SIZE.mini}
                    kind="tertiary"
                    onClick={() => markRead(row.id)}
                  >
                    标记已读
                  </Button>
                )
              }
            </TableBuilderColumn>
          </TableBuilder>
        )}
      </Block>
    </Block>
  );
}
