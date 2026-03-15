<template>
  <div class="reply-item level-2">
    <div class="reply-line">
      <span class="reply-author">{{ reply.username }}</span>
      <template v-if="reply.reply_to_user_id && reply.reply_to_user_id !== reply.user_id">
        <span class="reply-to-text">
          回复
          <span class="reply-target">{{ reply.reply_to_username || '用户' }}</span>
        </span>
      </template>
      <span class="reply-separator">：</span>
      <span class="reply-content">{{ reply.content }}</span>
      <span class="reply-time">{{ formatTime(reply.created_at) }}</span>
    </div>
    <div class="reply-actions">
      <el-button
        text
        size="small"
        @click="toggleReplyInput(reply.id, reply.user_id)"
        v-if="isLoggedIn()"
      >
        回复
      </el-button>
      <el-button
        v-if="reply.user_id === getCurrentUserId()"
        text
        size="small"
        @click="editComment(reply)"
      >
        编辑
      </el-button>
      <el-button
        v-if="reply.user_id === getCurrentUserId()"
        text
        size="small"
        @click="deleteComment(reply.id)"
      >
        删除
      </el-button>
    </div>
    <div v-if="replyingTo === reply.id && isLoggedIn()" class="reply-input-box">
      <el-input
        v-model="replyContent"
        type="textarea"
        :rows="2"
        placeholder="添加回复..."
        maxlength="500"
      />
      <div class="reply-input-actions">
        <el-button text @click="cancelReply">取消</el-button>
        <el-button type="primary" @click="submitReply(reply.id, reply.user_id)" :disabled="!replyContent.trim()">
          回复
        </el-button>
      </div>
    </div>
    <!-- 递归：子回复（支持多层回复链） -->
    <div v-if="reply.level2_replies && reply.level2_replies.length > 0" class="level-2-replies">
      <ReplyNode
        v-for="r in reply.level2_replies"
        :key="r.id"
        :reply="r"
      />
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue';

defineOptions({ name: 'ReplyNode' });

const props = defineProps({
  reply: { type: Object, required: true }
});

const replyingTo = inject('replyingTo');
const replyContent = inject('replyContent');
const formatTime = inject('formatTime');
const toggleReplyInput = inject('toggleReplyInput');
const submitReply = inject('submitReply');
const cancelReply = inject('cancelReply');
const getCurrentUserId = inject('getCurrentUserId');
const isLoggedIn = inject('isLoggedIn');
const editComment = inject('editComment');
const deleteComment = inject('deleteComment');
</script>
