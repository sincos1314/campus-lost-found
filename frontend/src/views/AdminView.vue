<template>
  <div class="admin-container">
    <el-card shadow="never">
      <div class="toolbar" v-if="isAdmin">
        <el-input
          v-model="keyword"
          placeholder="搜索用户名/标题"
          clearable
          class="toolbar-input"
          @keyup.enter="load"
        />
        <el-select
          v-model="reportStatus"
          placeholder="举报状态"
          class="toolbar-select"
          @change="load"
        >
          <el-option label="全部" value="" />
          <el-option label="已举报" value="open" />
          <el-option label="处理中" value="processing" />
          <el-option label="已解决" value="resolved" />
          <el-option label="已拒绝" value="rejected" />
          <el-option label="已撤回" value="withdrawn" />
        </el-select>
        <el-select
          v-model="itemStatus"
          placeholder="物品状态"
          class="toolbar-select"
          @change="load"
        >
          <el-option label="全部" value="" />
          <el-option label="进行中" value="open" />
          <el-option label="已解决" value="closed" />
        </el-select>
        <el-button type="primary" @click="load">刷新</el-button>
        <el-button type="success" v-if="meLevel" @click="openCreateUser"
          >创建用户</el-button
        >
        <el-button type="success" v-if="meLevel" @click="openCreateItem"
          >创建物品</el-button
        >
      </div>
      <div v-else class="user-stats-header">
        <h2>数据统计</h2>
        <p>查看平台基本统计数据</p>
      </div>
      <el-tabs v-model="tab">
        <el-tab-pane label="用户" name="users" v-if="isAdmin">
          <el-table :data="usersPaged" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column label="角色">
              <template #default="{ row }">
                <el-tag v-if="row.role === 'admin'" type="success"
                  >管理员</el-tag
                >
                <el-tag v-else>普通用户</el-tag>
                <el-tag
                  v-if="row.is_banned"
                  type="danger"
                  style="margin-left: 6px"
                  >已封禁</el-tag
                >
              </template>
            </el-table-column>
            <el-table-column label="等级">
              <template #default="{ row }">
                {{ row.role === "admin" ? levelText(row.admin_level) : "无" }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="420">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="danger"
                  v-if="!row.is_banned && !isSelf(row)"
                  @click="banUser(row)"
                  >封禁</el-button
                >
                <el-button
                  size="small"
                  type="success"
                  v-else-if="row.is_banned && !isSelf(row)"
                  @click="unbanUser(row)"
                  >解封</el-button
                >
                <el-button size="small" @click="viewUser(row)">详情</el-button>
                <el-button
                  size="small"
                  type="warning"
                  v-if="row.role !== 'admin' && canAppointLow && !isSelf(row)"
                  @click="appoint(row, 'low')"
                  >任命低级</el-button
                >
                <el-button
                  size="small"
                  type="warning"
                  v-if="row.role !== 'admin' && canAppointMid && !isSelf(row)"
                  @click="appoint(row, 'mid')"
                  >任命中级</el-button
                >
                <el-button
                  size="small"
                  type="danger"
                  v-if="canRevoke(row) && !isSelf(row)"
                  @click="revoke(row)"
                  >解除任命</el-button
                >
                <el-button
                  size="small"
                  type="danger"
                  v-if="canDelete(row) && !isSelf(row)"
                  @click="deleteUser(row)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="usersPage"
              :page-size="pageSize"
              :total="usersFiltered.length"
              @current-change="
                (p) => {
                  usersPage = p;
                }
              "
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="物品" name="items" v-if="isAdmin">
          <el-table :data="itemsPaged" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="title" label="标题" />
            <el-table-column label="类型">
              <template #default="{ row }">
                <el-tag>{{ categoryText(row.category) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'closed' ? 'success' : 'warning'"
                  >{{ statusText(row.status) }}</el-tag
                >
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="success"
                  v-if="row.status !== 'closed'"
                  @click="updateItemStatus(row, 'closed')"
                  >标记已解决</el-button
                >
                <el-button
                  size="small"
                  type="warning"
                  v-else
                  @click="updateItemStatus(row, 'open')"
                  >标记进行中</el-button
                >
                <el-button size="small" @click="viewItem(row)">详情</el-button>
                <el-button
                  size="small"
                  type="danger"
                  v-if="canDeleteItem"
                  @click="deleteItem(row)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="itemsPage"
              :page-size="pageSize"
              :total="itemsFiltered.length"
              @current-change="
                (p) => {
                  itemsPage = p;
                }
              "
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="举报" name="reports" v-if="isAdmin">
          <el-table :data="reportsPaged" style="width: 100%" class="reports-table">
            <el-table-column prop="id" label="ID" width="80" class-name="report-cell" />
            <el-table-column label="举报类别" min-width="100" class-name="report-cell">
              <template #default="{ row }">{{
                reportCategoryText(row.category)
              }}</template>
            </el-table-column>
            <el-table-column label="严重级" min-width="80" class-name="report-cell">
              <template #default="{ row }">{{
                severityText(row.severity)
              }}</template>
            </el-table-column>
            <el-table-column label="状态" width="195" class-name="report-cell">
              <template #default="{ row }">
                <el-select
                  :model-value="row.status"
                  @update:model-value="handleStatusChange(row, $event)"
                  placeholder="设置状态"
                  :disabled="row.user_withdrawn || row.status === 'withdrawn'"
                  style="width: 100%"
                >
                  <!-- 当状态是 open 时，添加"已举报"选项用于显示（disabled，不可选） -->
                  <el-option 
                    v-if="row.status === 'open' && !row.user_withdrawn"
                    label="已举报" 
                    value="open"
                    disabled
                  />
                  <!-- 当状态是 withdrawn 时，添加"举报已撤回"选项用于显示（disabled，不可选） -->
                  <el-option 
                    v-if="row.user_withdrawn || row.status === 'withdrawn'"
                    label="举报已撤回" 
                    value="withdrawn"
                    disabled
                  />
                  <!-- 可选择的选项 -->
                  <el-option label="处理中" value="processing" />
                  <el-option label="已解决" value="resolved" />
                  <el-option label="已拒绝" value="rejected" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" min-width="150" class-name="report-cell" show-overflow-tooltip />
            <el-table-column label="被举报物品" min-width="180" class-name="report-cell">
              <template #default="{ row }">
                <a
                  v-if="row.item_id"
                  @click="gotoItem(row)"
                  class="report-item-link"
                >
                  {{ row.item_title || "物品#" + row.item_id }}（{{
                    categoryText(row.item_category)
                  }}）
                </a>
                <span v-else>无</span>
              </template>
            </el-table-column>
            <el-table-column label="举报用户" min-width="150" class-name="report-cell">
              <template #default="{ row }">
                <span v-if="row.anonymous">此用户为匿名举报</span>
                <span v-else>{{ row.reporter_username || ('用户#'+row.reporter_id) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="被举报用户" min-width="150" class-name="report-cell">
              <template #default="{ row }">
                <span>{{ row.target_username || (row.target_user_id ? ('用户#'+row.target_user_id) : '无') }}</span>
              </template>
            </el-table-column>
            <el-table-column label="证据" width="180" class-name="report-cell">
              <template #default="{ row }">
                <div v-if="getEvidenceImages(row).length > 0" class="evidence-image-container">
                  <el-image
                    :src="absoluteUrl(getCurrentEvidenceImage(row))"
                    :preview-src-list="getEvidencePreviewList(row)"
                    style="width: 60px; height: 60px; z-index: 3000"
                    :preview-teleported="true"
                  />
                  <div v-if="getEvidenceImages(row).length > 1" class="evidence-controls">
                    <el-button
                      size="small"
                      circle
                      :disabled="getCurrentEvidenceIndex(row) === 0"
                      @click.stop="prevEvidenceImage(row)"
                      class="evidence-nav-btn"
                    >
                      &lt;
                    </el-button>
                    <span class="evidence-counter">
                      {{ getCurrentEvidenceIndex(row) + 1 }}/{{ getEvidenceImages(row).length }}
                    </span>
                    <el-button
                      size="small"
                      circle
                      :disabled="getCurrentEvidenceIndex(row) === getEvidenceImages(row).length - 1"
                      @click.stop="nextEvidenceImage(row)"
                      class="evidence-nav-btn"
                    >
                      &gt;
                    </el-button>
                  </div>
                </div>
                <span v-else>无</span>
              </template>
            </el-table-column>
            <el-table-column label="处理" min-width="400" class-name="report-cell">
              <template #default="{ row }">
                <el-input
                  v-model="row.resolution_note"
                  placeholder="处理备注"
                  @change="updateReportStatus(row, row.status)"
                  :disabled="row.user_withdrawn || row.status === 'withdrawn'"
                  style="width: 100%"
                />
                <div
                  style="
                    margin-top: 6px;
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                  "
                >
                  <el-button
                    v-if="row.item_id"
                    type="danger"
                    size="small"
                    @click="adminDeleteReportedItem(row)"
                  >
                    删除此{{ categoryText(row.item_category) }}信息
                  </el-button>
                  <el-button
                    v-if="row.target_user_id"
                    type="warning"
                    size="small"
                    @click="adminBanReportedUser(row)"
                    >封禁被举报用户</el-button
                  >
                  <el-button
                    v-if="row.reporter_id"
                    type="warning"
                    size="small"
                    @click="adminBanReporter(row)"
                    >封禁举报用户</el-button
                  >
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="reportsPage"
              :page-size="pageSize"
              :total="reportsFiltered.length"
              @current-change="
                (p) => {
                  reportsPage = p;
                }
              "
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="统计" name="stats">
          <div class="stats">
            <el-card 
              class="stat-card" 
              v-for="(v, k) in filteredStats" 
              :key="k"
            >
              <div class="stat-title">{{ statText(k) }}</div>
              <div class="stat-value">{{ v }}</div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    <el-dialog v-model="userDialog" title="用户详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="头像">
              <el-avatar
                :size="60"
                :src="currentUser?.avatar_url ? absoluteUrl(currentUser.avatar_url) : ''"
              />
        </el-descriptions-item>
        <el-descriptions-item label="用户名">{{
          currentUser?.username
        }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{
          currentUser?.email
        }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{
          currentUser?.phone || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="院系">{{
          currentUser?.department || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="年级">{{
          currentUser?.grade_display || currentUser?.grade || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{
          currentUser?.class_name || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{
          currentUser?.student_id || "未填写"
        }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{
          genderText(currentUser?.gender)
        }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{
          roleText(currentUser?.role)
        }}</el-descriptions-item>
        <el-descriptions-item label="等级">{{
          levelText(currentUser?.admin_level)
        }}</el-descriptions-item>
        <el-descriptions-item label="加入时间">{{
          currentUser?.created_at
        }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
    <el-dialog v-model="itemDialog" title="物品详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{
          currentItem?.title
        }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{
          categoryText(currentItem?.category)
        }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{
          statusText(currentItem?.status)
        }}</el-descriptions-item>
        <el-descriptions-item label="物品类型">{{
          currentItem?.item_type
        }}</el-descriptions-item>
        <el-descriptions-item label="地点">{{
          currentItem?.location
        }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{
          currentItem?.contact_name
        }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{
          currentItem?.contact_phone
        }}</el-descriptions-item>
        <el-descriptions-item label="日期">{{
          currentItem?.date
        }}</el-descriptions-item>
        <el-descriptions-item label="发布人">{{
          currentItem?.username
        }}</el-descriptions-item>
        <el-descriptions-item label="发布时间">{{
          currentItem?.created_at
        }}</el-descriptions-item>
        <el-descriptions-item label="图片">
          <img
            v-if="currentItem?.image_url"
            :src="absoluteUrl(currentItem.image_url)"
            style="max-width: 100%; border-radius: 8px"
          />
          <span v-else>无图片</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
    <el-dialog v-model="createUserDialog" title="创建用户" width="600px">
      <el-form :model="newUser" label-width="100px">
        <el-form-item label="身份">
          <el-select v-model="newUser.identity" placeholder="请选择">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="newUser.identity==='teacher'" label="工号"><el-input v-model="newUser.staff_id" /></el-form-item>
        <el-form-item label="用户名"><el-input v-model="newUser.username" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="newUser.email" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="newUser.phone" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="newUser.password" type="password" show-password /></el-form-item>
        <template v-if="newUser.identity==='student'">
          <el-form-item label="院系"><el-input v-model="newUser.department" /></el-form-item>
          <el-form-item label="年级">
            <el-select v-model="newUser.grade" placeholder="选择年级">
              <el-option label="大一" value="大一" />
              <el-option label="大二" value="大二" />
              <el-option label="大三" value="大三" />
              <el-option label="大四" value="大四" />
            </el-select>
          </el-form-item>
          <el-form-item label="班级"><el-input v-model="newUser.class_name" /></el-form-item>
          <el-form-item label="学号"><el-input v-model="newUser.student_id" /></el-form-item>
          <el-form-item label="性别">
            <el-select v-model="newUser.gender" placeholder="选择性别(可选)">
              <el-option label="男" value="male" />
              <el-option label="女" value="female" />
              <el-option label="其他" value="other" />
              <el-option label="不透露" value="secret" />
            </el-select>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="createUserDialog=false">取消</el-button>
        <el-button type="primary" @click="submitCreateUser">创建</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="createItemDialog" title="创建物品" width="600px">
      <el-form :model="newItem" label-width="120px">
        <el-form-item label="归属用户ID"
          ><el-input v-model="newItem.user_id"
        /></el-form-item>
        <el-form-item label="标题"
          ><el-input v-model="newItem.title"
        /></el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="newItem.description"
            type="textarea"
            :rows="5"
            placeholder="详细描述物品特征、品牌、颜色等信息，便于识别"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newItem.category">
            <el-option label="失物" value="lost" />
            <el-option label="拾物" value="found" />
          </el-select>
        </el-form-item>
        <el-form-item label="物品类型">
          <el-select v-model="newItem.item_type" placeholder="请选择物品类型">
            <el-option label="手机" value="手机" />
            <el-option label="钱包" value="钱包" />
            <el-option label="钥匙" value="钥匙" />
            <el-option label="身份证/学生证" value="身份证/学生证" />
            <el-option label="书籍" value="书籍" />
            <el-option label="衣物" value="衣物" />
            <el-option label="电子产品" value="电子产品" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="地点"
          ><el-input v-model="newItem.location"
        /></el-form-item>
        <el-form-item label="联系人"
          ><el-input v-model="newItem.contact_name"
        /></el-form-item>
        <el-form-item label="联系电话"
          ><el-input v-model="newItem.contact_phone"
        /></el-form-item>
        <el-form-item label="日期"
          ><el-date-picker
            v-model="newItem.date"
            type="date"
            value-format="YYYY-MM-DD"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createItemDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreateItem">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from "vue";
import request, { absoluteUrl, previewList, previewListMultiple } from "../utils/request";
import { getUser } from "../utils/auth";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
const router = useRouter();
const tab = ref("users");
const users = ref([]);
const items = ref([]);
const reports = ref([]);
const stats = ref({});
const keyword = ref("");
const reportStatus = ref("");
const itemStatus = ref("");
const userDialog = ref(false);
const itemDialog = ref(false);
const currentUser = ref(null);
const currentItem = ref(null);
const pageSize = ref(10);
const usersPage = ref(1);
const itemsPage = ref(1);
const reportsPage = ref(1);
// 存储每个举报的当前证据图片索引
const evidenceImageIndices = ref({});
const me = getUser();
const isAdmin = computed(() => me?.role === 'admin');
const meLevel = me?.admin_level || "";
const meId = me?.id || 0;
const canAppointLow = computed(() => meLevel === "mid" || meLevel === "high");
const canAppointMid = computed(() => meLevel === "high");
const canDeleteItem = computed(() => meLevel === "mid" || meLevel === "high");
const isSelf = (row) => row?.id === meId;
const canDelete = (row) => {
  if (!meLevel) return false;
  if (row.role === "admin" && row.admin_level) {
    const r = { low: 1, mid: 2, high: 3 };
    return r[meLevel] > r[row.admin_level];
  }
  return meLevel !== "low";
};
const canRevoke = (row) => {
  if (row.role !== "admin" || !row.admin_level) return false;
  if (!row.admin_appointed_by || row.admin_appointed_by !== meId) return false;
  if (row.admin_level === "low") return meLevel === "mid" || meLevel === "high";
  if (row.admin_level === "mid") return meLevel === "high";
  return false;
};
const categoryText = (c) =>
  c === "lost" ? "失物" : c === "found" ? "拾物" : c || "";
const statusText = (s) => (s === "closed" ? "已解决" : "进行中");
const roleText = (r) =>
  r === "admin" ? "管理员" : r === "banned" ? "已封禁" : "普通用户";
const genderText = (g) =>
  ({ male: "男", female: "女", other: "其他", secret: "不透露" }[g] ||
  "未填写");
const levelText = (l) =>
  ({ low: "低级", mid: "中级", high: "高级" }[l] || "无");
const statText = (k) =>
  ({
    users: "用户总数",
    items: "物品总数",
    lost: "失物数量",
    found: "拾物数量",
    closed: "已解决数量",
    reports_open: "未处理举报",
  }[k] || k);

// 获取举报的所有证据图片
const getEvidenceImages = (row) => {
  if (row.evidence_image_urls && Array.isArray(row.evidence_image_urls) && row.evidence_image_urls.length > 0) {
    return row.evidence_image_urls;
  } else if (row.evidence_image_url) {
    return [row.evidence_image_url];
  }
  return [];
};

// 获取当前显示的证据图片
const getCurrentEvidenceImage = (row) => {
  const images = getEvidenceImages(row);
  if (images.length === 0) return '';
  const index = getCurrentEvidenceIndex(row);
  return images[index] || images[0];
};

// 获取当前证据图片索引
const getCurrentEvidenceIndex = (row) => {
  if (!evidenceImageIndices.value[row.id]) {
    evidenceImageIndices.value[row.id] = 0;
  }
  return evidenceImageIndices.value[row.id];
};

// 获取证据图片预览列表
const getEvidencePreviewList = (row) => {
  const images = getEvidenceImages(row);
  return previewListMultiple(images);
};

// 上一张证据图片
const prevEvidenceImage = (row) => {
  const images = getEvidenceImages(row);
  if (images.length <= 1) return;
  const currentIndex = getCurrentEvidenceIndex(row);
  if (currentIndex > 0) {
    evidenceImageIndices.value[row.id] = currentIndex - 1;
  }
};

// 下一张证据图片
const nextEvidenceImage = (row) => {
  const images = getEvidenceImages(row);
  if (images.length <= 1) return;
  const currentIndex = getCurrentEvidenceIndex(row);
  if (currentIndex < images.length - 1) {
    evidenceImageIndices.value[row.id] = currentIndex + 1;
  }
};

// 普通用户只能看到部分统计信息
const filteredStats = computed(() => {
  if (isAdmin.value) {
    return stats.value;
  }
  // 普通用户只能看到：用户总数、已解决数量、物品总数、失物数量、拾物数量
  const allowedKeys = ['users', 'closed', 'items', 'lost', 'found'];
  const filtered = {};
  Object.keys(stats.value).forEach(key => {
    if (allowedKeys.includes(key)) {
      filtered[key] = stats.value[key];
    }
  });
  return filtered;
});

const load = async () => {
  try {
    if (isAdmin.value) {
      if (tab.value === "users") users.value = await request.get("/admin/users");
      if (tab.value === "items") items.value = await request.get("/admin/items");
      if (tab.value === "reports")
        reports.value = await request.get("/admin/reports", {
          params: { status: reportStatus.value },
        });
    }
    if (tab.value === "stats") {
      try {
        stats.value = await request.get("/admin/stats");
      } catch (error) {
        if (error.response?.status === 403) {
          ElMessage.error('您没有权限访问数据看板，仅管理员可访问');
          // 如果不是管理员，重定向到首页
          if (!isAdmin.value) {
            setTimeout(() => {
              router.push('/');
            }, 1500);
          }
        } else {
          throw error;
        }
      }
    }
  } catch (error) {
    console.error('加载数据失败:', error);
    if (error.response?.status !== 403) {
      ElMessage.error('加载数据失败');
    }
  }
};

onMounted(() => {
  // 普通用户默认显示统计页面
  if (!isAdmin.value) {
    tab.value = "stats";
  }
  load();
});
watch(tab, load);

const banUser = async (row) => {
  await request.put(`/admin/users/${row.id}/ban`, { ban: true });
  await load();
};
const unbanUser = async (row) => {
  await request.put(`/admin/users/${row.id}/ban`, { ban: false });
  await load();
};
const updateItemStatus = async (row, status) => {
  await request.put(`/admin/items/${row.id}/status`, { status });
  await load();
};
const updateReportStatus = async (row, status = null) => {
  // 使用传入的 status 参数，如果没有则使用 row.status
  const targetStatus = status !== null ? status : row.status;
  
  // 如果状态是 open 或 withdrawn，不允许更新（这些是显示用的）
  if (targetStatus === 'open' || targetStatus === 'withdrawn' || row.user_withdrawn) {
    return;
  }
  try {
    await request.put(`/admin/reports/${row.id}`, {
      status: targetStatus,
      resolution_note: row.resolution_note,
    });
    ElMessage.success('状态已更新');
  } catch (error) {
    console.error('更新状态失败:', error);
    ElMessage.error('更新状态失败');
    // 重新加载数据以恢复原状态
    if (tab.value === 'reports') {
      await load();
    }
  }
};
const adminDeleteReportedItem = async (row) => {
  await request.delete(`/admin/items/${row.item_id}`);
  await load();
};
const adminBanReportedUser = async (row) => {
  await request.put(`/admin/users/${row.target_user_id}/ban`, { ban: true });
  ElMessage.success(`已封禁被举报用户（${row.target_username || ("用户#" + row.target_user_id)}）`);
  await load();
};
const adminBanReporter = async (row) => {
  await request.put(`/admin/users/${row.reporter_id}/ban`, { ban: true });
  if (row.anonymous) {
    ElMessage.success('已封禁举报用户');
  } else {
    ElMessage.success(`已封禁举报用户（${row.reporter_username || ("用户#" + row.reporter_id)}）`);
  }
  await load();
};
const gotoItem = (row) => {
  router.push(`/item/${row.item_id}`);
};
const reportCategoryText = (c) =>
  ({ spam: "垃圾信息", abuse: "骚扰/辱骂", fake: "虚假信息", other: "其他" }[
    c
  ] || c);
const severityText = (s) => ({ low: "低", medium: "中", high: "高" }[s] || s);
// 注意：statusReportText 函数可能在其他地方使用，暂时保留
const statusReportText = (st, withdrawn) => {
  if (withdrawn || st === "withdrawn") return "举报已撤回";
  return (
    {
      open: "已举报",
      processing: "处理中",
      resolved: "已解决",
      rejected: "已拒绝",
    }[st] || st
  );
};


// 处理状态下拉框的值变化
const handleStatusChange = async (row, newValue) => {
  // 如果选择的是 open 或 withdrawn，不允许（这些是显示用的，不可选）
  if (newValue === 'open' || newValue === 'withdrawn') {
    // 不更新状态，保持原值
    return;
  }
  // 更新状态
  row.status = newValue;
  await updateReportStatus(row, newValue);
};
const appoint = async (row, level) => {
  await request.post("/admin/appoint", { target_user_id: row.id, level });
  await load();
};
const revoke = async (row) => {
  await request.post("/admin/revoke", { target_user_id: row.id });
  await load();
};
const deleteUser = async (row) => {
  await request.delete(`/admin/users/${row.id}`);
  await load();
};
const deleteItem = async (row) => {
  await request.delete(`/admin/items/${row.id}`);
  await load();
};

const createUserDialog = ref(false);
const createItemDialog = ref(false);
const newUser = ref({
  identity: "student",
  staff_id: "",
  username: "",
  email: "",
  phone: "",
  password: "",
  department: "",
  grade: "",
  class_name: "",
  student_id: "",
  gender: "",
});
const newItem = ref({
  user_id: "",
  title: "",
  description: "",
  category: "lost",
  item_type: "",
  location: "",
  contact_name: "",
  contact_phone: "",
  date: "",
});
const openCreateUser = () => {
  createUserDialog.value = true;
};
const openCreateItem = () => {
  createItemDialog.value = true;
};
const submitCreateUser = async () => {
  await request.post("/admin/users/create", newUser.value);
  createUserDialog.value = false;
  newUser.value = {
    identity: "student",
    staff_id: "",
    username: "",
    email: "",
    phone: "",
    password: "",
    department: "",
    grade: "",
    class_name: "",
    student_id: "",
    gender: "",
  };
  await load();
};
const submitCreateItem = async () => {
  await request.post("/admin/items/create", newItem.value);
  createItemDialog.value = false;
  newItem.value = {
    user_id: "",
    title: "",
    description: "",
    category: "lost",
    item_type: "手机",
    location: "",
    contact_name: "",
    contact_phone: "",
    date: "",
  };
  await load();
};

const usersFiltered = computed(() => {
  if (!keyword.value) return users.value;
  return users.value.filter(
    (u) =>
      (u.username || "").includes(keyword.value) ||
      (u.email || "").includes(keyword.value)
  );
});
const usersPaged = computed(() => {
  const start = (usersPage.value - 1) * pageSize.value;
  return usersFiltered.value.slice(start, start + pageSize.value);
});
const itemsFiltered = computed(() => {
  let list = items.value;
  if (itemStatus.value)
    list = list.filter((i) => i.status === itemStatus.value);
  if (!keyword.value) return list;
  return list.filter((i) => (i.title || "").includes(keyword.value));
});
const itemsPaged = computed(() => {
  const start = (itemsPage.value - 1) * pageSize.value;
  return itemsFiltered.value.slice(start, start + pageSize.value);
});
const reportsFiltered = computed(() => {
  if (!keyword.value) return reports.value;
  return reports.value.filter(
    (r) =>
      (r.description || "").includes(keyword.value) ||
      (r.category || "").includes(keyword.value)
  );
});
const reportsPaged = computed(() => {
  const start = (reportsPage.value - 1) * pageSize.value;
  return reportsFiltered.value.slice(start, start + pageSize.value);
});
const viewUser = (row) => {
  currentUser.value = row;
  userDialog.value = true;
};
const viewItem = (row) => {
  currentItem.value = row;
  itemDialog.value = true;
};
</script>

<style scoped>
.admin-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.admin-container :deep(.el-card) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 1.5rem;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.stat-card {
  text-align: center;
}
.stat-title {
  font-weight: 700;
  color: var(--color-text);
}
.stat-value {
  font-size: 24px;
  font-weight: 900;
  color: var(--color-text);
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 12px 0;
}

.toolbar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.user-stats-header {
  margin-bottom: 2rem;
  text-align: center;
}

.user-stats-header h2 {
  font-size: 2rem;
  font-weight: 900;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.user-stats-header p {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 600;
}

/* 移除 Element Plus 默认的输入框包装器样式 */
.admin-container :deep(.el-input),
.admin-container :deep(.el-select) {
  border: none !important;
  box-shadow: none !important;
}

.admin-container :deep(.el-input__wrapper),
.admin-container :deep(.el-select__wrapper) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

.admin-container :deep(.el-input__inner),
.admin-container :deep(.el-select__placeholder),
.admin-container :deep(.el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

.admin-container :deep(.el-input__wrapper.is-focus),
.admin-container :deep(.el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.admin-container :deep(.el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.admin-container :deep(.el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

.admin-container :deep(.el-button--success) {
  background: #48bb78;
  color: white !important;
}

.admin-container :deep(.el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

/* 证据图片容器样式 */
.evidence-image-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.evidence-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.evidence-nav-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  font-size: 14px;
  font-weight: 700;
  border: var(--border-width) solid var(--border-color);
  border-radius: 50%;
  background: var(--color-card);
  color: var(--color-text);
  transition: all 0.15s ease;
}

.evidence-nav-btn:hover:not(:disabled) {
  background: var(--color-accent);
  color: white;
  transform: translateY(-2px);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.evidence-nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.evidence-counter {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text);
  min-width: 40px;
  text-align: center;
}

/* 确保图片预览不被遮挡 */
.admin-container :deep(.el-image-viewer__wrapper) {
  z-index: 9999 !important;
}

.admin-container :deep(.el-image-viewer__mask) {
  z-index: 9998 !important;
}

/* 状态显示文本样式 */
.status-display-text {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-text);
  background: var(--color-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  min-width: 80px;
  text-align: center;
}

.status-display-text.withdrawn-status {
  color: #f56565;
  background: rgba(245, 101, 101, 0.1);
}

/* 状态下拉框样式 */
.admin-container :deep(.el-table .el-select) {
  width: 100%;
}

.admin-container :deep(.el-table .el-select.is-disabled .el-input__inner) {
  color: var(--color-text);
  cursor: not-allowed;
}

/* 禁用选项的样式（用于显示"已举报"和"举报已撤回"） */
.admin-container :deep(.el-table .el-select .el-option.is-disabled) {
  color: var(--color-text);
  cursor: default;
}

.admin-container :deep(.el-table .el-select .el-option.is-disabled.selected) {
  color: var(--color-text);
  background-color: var(--color-primary);
}

/* 举报表格样式优化 */
.admin-container :deep(.reports-table) {
  table-layout: auto;
}

.admin-container :deep(.reports-table .report-cell) {
  padding: 12px 16px !important;
  word-wrap: break-word;
  word-break: break-all;
  white-space: normal;
  line-height: 1.6;
  vertical-align: top;
}

/* 状态列特殊处理 - 减少padding以给下拉框更多空间 */
.admin-container :deep(.reports-table .el-table__cell[data-label="状态"]) {
  padding: 12px 8px !important;
}

.admin-container :deep(.reports-table .el-table__cell) {
  padding: 12px 16px !important;
}

.admin-container :deep(.reports-table .el-table__header .el-table__cell) {
  padding: 12px 16px !important;
  font-weight: 700;
  background: var(--color-primary);
  color: var(--color-text);
}

/* 举报表格中的链接样式 */
.admin-container :deep(.reports-table .report-item-link) {
  color: var(--color-accent);
  text-decoration: none;
  cursor: pointer;
  white-space: normal;
  word-wrap: break-word;
  word-break: break-all;
  text-align: left;
  line-height: 1.6;
  padding: 0;
  border: none;
  background: transparent;
  box-shadow: none;
  font-weight: 400;
}

.admin-container :deep(.reports-table .report-item-link:hover) {
  color: var(--color-accent);
  text-decoration: underline;
  border: none;
  box-shadow: none;
  background: transparent;
}

/* 处理字段中的按钮容器 */
.admin-container :deep(.reports-table .el-table__cell > div[style*="margin-top"]) {
  margin-top: 8px !important;
  gap: 8px !important;
}

/* 确保表格单元格内容可以换行 */
.admin-container :deep(.reports-table td) {
  white-space: normal !important;
  word-wrap: break-word !important;
  word-break: break-all !important;
}

/* 处理备注输入框样式 */
.admin-container :deep(.reports-table .el-input) {
  width: 100%;
}

.admin-container :deep(.reports-table .el-input__wrapper) {
  width: 100%;
}

/* 状态下拉框样式 - 确保内容完整显示 */
.admin-container :deep(.reports-table .el-select) {
  width: 100% !important;
  min-width: 150px;
}

.admin-container :deep(.reports-table .el-select__wrapper) {
  width: 100% !important;
  min-width: 150px;
}

.admin-container :deep(.reports-table .el-select__selected-item) {
  white-space: nowrap !important;
  overflow: visible !important;
  text-overflow: clip !important;
  max-width: none !important;
  width: auto !important;
  display: inline-block !important;
  padding-right: 20px !important;
}

.admin-container :deep(.reports-table .el-select .el-input__inner) {
  width: 100% !important;
  min-width: 150px;
  padding-right: 30px !important;
}

.admin-container :deep(.reports-table .el-select__placeholder) {
  white-space: nowrap;
}

/* 确保状态下拉框单元格有足够空间 */
.admin-container :deep(.reports-table .el-table__cell[data-label="状态"]) {
  min-width: 160px !important;
  width: 160px !important;
  padding: 12px 8px !important;
}

/* 确保下拉框在单元格内完整显示 */
.admin-container :deep(.reports-table .el-table__cell[data-label="状态"] .el-select) {
  max-width: 100%;
  box-sizing: border-box;
}

/* 优化表格行间距和整体布局 */
.admin-container :deep(.reports-table .el-table__row) {
  height: auto;
  min-height: 60px;
}

.admin-container :deep(.reports-table .el-table__body tr:hover > td) {
  background-color: var(--color-primary);
  opacity: 0.8;
}

/* 确保表格列宽自适应 */
.admin-container :deep(.reports-table .el-table__body-wrapper) {
  overflow-x: auto;
}

/* 优化说明字段的显示 */
.admin-container :deep(.reports-table .el-table__cell[data-label="说明"]) {
  max-width: 200px;
}

/* 优化按钮组布局 */
.admin-container :deep(.reports-table .el-table__cell > div[style*="display: flex"]) {
  flex-wrap: wrap;
  align-items: flex-start;
}

.admin-container :deep(.reports-table .el-button--small) {
  margin: 2px;
  white-space: nowrap;
}

.admin-container :deep(.el-table) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
}

.admin-container :deep(.el-table th) {
  background: var(--color-primary);
  color: var(--color-text);
  font-weight: 900;
}

/* 对话框中的输入框样式 */
.admin-container :deep(.el-dialog) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.admin-container :deep(.el-dialog .el-input),
.admin-container :deep(.el-dialog .el-select),
.admin-container :deep(.el-dialog .el-textarea),
.admin-container :deep(.el-dialog .el-date-editor) {
  border: none !important;
  box-shadow: none !important;
}

.admin-container :deep(.el-dialog .el-input__wrapper),
.admin-container :deep(.el-dialog .el-select__wrapper),
.admin-container :deep(.el-dialog .el-textarea__inner) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

.admin-container :deep(.el-dialog .el-input__inner),
.admin-container :deep(.el-dialog .el-textarea__inner) {
  /* textarea 的 inner 需要保持边框 */
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 0.6rem 1rem !important;
}

.admin-container :deep(.el-dialog .el-select__placeholder),
.admin-container :deep(.el-dialog .el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

.admin-container :deep(.el-dialog .el-input__wrapper.is-focus),
.admin-container :deep(.el-dialog .el-textarea__inner:focus),
.admin-container :deep(.el-dialog .el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

/* 确保 textarea 的 focus 状态也有阴影效果 */
.admin-container :deep(.el-dialog .el-textarea__inner:focus) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.admin-container :deep(.el-dialog .el-date-editor .el-input__wrapper) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
}

.admin-container :deep(.el-dialog .el-date-editor .el-input__wrapper.is-focus) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
}
</style>
