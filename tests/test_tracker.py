#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import numpy as np
from scipy.optimize import linear_sum_assignment


class BoundingBox:
    """テスト用のバウンディングボックスクラス"""
    def __init__(self, x1, y1, x2, y2, label=None, track_id=None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.label = label
        self.track_id = track_id
        self.is_tracked = False

    def get_coords(self):
        return (self.x1, self.y1, self.x2, self.y2)


class TestTrackerCore(unittest.TestCase):
    """追跡アルゴリズムのコア機能のテスト"""
    
    def setUp(self):
        """テストの初期設定"""
        self.iou_threshold = 0.4
    
    def calculate_iou(self, box1, box2):
        """2つのバウンディングボックス間のIOUを計算"""
        x1_1, y1_1, x2_1, y2_1 = box1.get_coords()
        x1_2, y1_2, x2_2, y2_2 = box2.get_coords()
        
        # 交差領域の計算
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # 各ボックスの面積
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        
        # Union面積
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def test_iou_calculation_perfect_overlap(self):
        """完全に重なるボックスのIOU計算テスト"""
        box1 = BoundingBox(0, 0, 100, 100)
        box2 = BoundingBox(0, 0, 100, 100)
        iou = self.calculate_iou(box1, box2)
        self.assertEqual(iou, 1.0)
    
    def test_iou_calculation_no_overlap(self):
        """重ならないボックスのIOU計算テスト"""
        box1 = BoundingBox(0, 0, 100, 100)
        box2 = BoundingBox(200, 200, 300, 300)
        iou = self.calculate_iou(box1, box2)
        self.assertEqual(iou, 0.0)
    
    def test_iou_calculation_partial_overlap(self):
        """部分的に重なるボックスのIOU計算テスト"""
        box1 = BoundingBox(0, 0, 100, 100)
        box2 = BoundingBox(50, 50, 150, 150)
        iou = self.calculate_iou(box1, box2)
        # 交差領域: 50x50 = 2500
        # Union: 10000 + 10000 - 2500 = 17500
        expected_iou = 2500 / 17500
        self.assertAlmostEqual(iou, expected_iou, places=5)
    
    def test_iou_threshold_acceptance(self):
        """IOUしきい値による追跡可否判定テスト"""
        box1 = BoundingBox(0, 0, 100, 100)
        # IOU = 0.4となるようなボックス
        # 必要な交差面積: 0.4 * union = 0.4 * (10000 + 10000 - intersection)
        # intersection = 0.4 * (20000 - intersection)
        # intersection = 8000 - 0.4 * intersection
        # 1.4 * intersection = 8000
        # intersection ≈ 5714.29
        # √5714.29 ≈ 75.6
        box2 = BoundingBox(24, 24, 100, 100)  # 約76x76の交差領域
        iou = self.calculate_iou(box1, box2)
        self.assertGreaterEqual(iou, self.iou_threshold)
    
    def test_iou_threshold_rejection(self):
        """IOUしきい値を下回る場合の追跡拒否テスト"""
        box1 = BoundingBox(0, 0, 100, 100)
        box2 = BoundingBox(70, 70, 170, 170)  # IOU < 0.4
        iou = self.calculate_iou(box1, box2)
        self.assertLess(iou, self.iou_threshold)


class TestHungarianMatching(unittest.TestCase):
    """ハンガリアンアルゴリズムによるマッチングのテスト"""
    
    def setUp(self):
        self.iou_threshold = 0.4
    
    def create_cost_matrix(self, prev_boxes, curr_boxes):
        """IOUベースのコスト行列を作成（1-IOUでコスト化）"""
        n_prev = len(prev_boxes)
        n_curr = len(curr_boxes)
        cost_matrix = np.ones((n_prev, n_curr))
        
        for i, prev_box in enumerate(prev_boxes):
            for j, curr_box in enumerate(curr_boxes):
                iou = TestTrackerCore().calculate_iou(prev_box, curr_box)
                cost_matrix[i, j] = 1 - iou  # IOUが高いほどコストが低い
        
        return cost_matrix
    
    def test_one_to_one_matching(self):
        """1対1の完全マッチングテスト"""
        prev_boxes = [
            BoundingBox(0, 0, 100, 100, label="cow1", track_id=1),
            BoundingBox(200, 0, 300, 100, label="cow2", track_id=2)
        ]
        curr_boxes = [
            BoundingBox(5, 5, 105, 105),  # cow1とほぼ同じ位置
            BoundingBox(205, 5, 305, 105)  # cow2とほぼ同じ位置
        ]
        
        cost_matrix = self.create_cost_matrix(prev_boxes, curr_boxes)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # 正しくマッチングされているか確認
        self.assertEqual(len(row_ind), 2)
        self.assertEqual(row_ind[0], 0)
        self.assertEqual(col_ind[0], 0)
        self.assertEqual(row_ind[1], 1)
        self.assertEqual(col_ind[1], 1)
    
    def test_partial_matching_with_threshold(self):
        """しきい値を考慮した部分マッチングテスト"""
        prev_boxes = [
            BoundingBox(0, 0, 100, 100, label="cow1", track_id=1),
            BoundingBox(200, 0, 300, 100, label="cow2", track_id=2)
        ]
        curr_boxes = [
            BoundingBox(5, 5, 105, 105),  # cow1とマッチ
            BoundingBox(400, 400, 500, 500)  # どれともマッチしない
        ]
        
        cost_matrix = self.create_cost_matrix(prev_boxes, curr_boxes)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # しきい値を適用してフィルタリング
        valid_matches = []
        for i, j in zip(row_ind, col_ind):
            iou = 1 - cost_matrix[i, j]
            if iou >= self.iou_threshold:
                valid_matches.append((i, j))
        
        # cow1のみがマッチするはず
        self.assertEqual(len(valid_matches), 1)
        self.assertEqual(valid_matches[0], (0, 0))
    
    def test_no_matches(self):
        """マッチが存在しない場合のテスト"""
        prev_boxes = [
            BoundingBox(0, 0, 100, 100, label="cow1", track_id=1)
        ]
        curr_boxes = [
            BoundingBox(400, 400, 500, 500)  # 完全に離れた位置
        ]
        
        cost_matrix = self.create_cost_matrix(prev_boxes, curr_boxes)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # しきい値チェック
        valid_matches = []
        for i, j in zip(row_ind, col_ind):
            iou = 1 - cost_matrix[i, j]
            if iou >= self.iou_threshold:
                valid_matches.append((i, j))
        
        self.assertEqual(len(valid_matches), 0)


class TestTrackingScenarios(unittest.TestCase):
    """実際の追跡シナリオのテスト"""
    
    def setUp(self):
        self.iou_threshold = 0.4
        self.next_track_id = 1
    
    def assign_track_ids(self, prev_boxes, curr_boxes):
        """前フレームと現フレームのボックスをマッチングしてtrack_idを割り当て"""
        if not prev_boxes:
            # 初回フレーム：全てに新規IDを割り当て
            for box in curr_boxes:
                box.track_id = self.next_track_id
                self.next_track_id += 1
                box.is_tracked = False
            return
        
        # コスト行列作成とマッチング
        cost_matrix = TestHungarianMatching().create_cost_matrix(prev_boxes, curr_boxes)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # マッチした現フレームボックスのインデックスを記録
        matched_curr_indices = set()
        
        # しきい値を満たすマッチングを適用
        for i, j in zip(row_ind, col_ind):
            iou = 1 - cost_matrix[i, j]
            if iou >= self.iou_threshold:
                # 前フレームのtrack_idとラベルを継承
                curr_boxes[j].track_id = prev_boxes[i].track_id
                curr_boxes[j].label = prev_boxes[i].label
                curr_boxes[j].is_tracked = True
                matched_curr_indices.add(j)
        
        # マッチしなかった現フレームボックスに新規IDを割り当て
        for j, box in enumerate(curr_boxes):
            if j not in matched_curr_indices:
                box.track_id = self.next_track_id
                self.next_track_id += 1
                box.is_tracked = False
    
    def test_continuous_tracking_success(self):
        """連続追跡成功のシナリオテスト"""
        # next_track_idをリセット
        self.next_track_id = 1
        
        # フレーム1
        frame1_boxes = [
            BoundingBox(0, 0, 100, 100, label="eating")
        ]
        self.assign_track_ids([], frame1_boxes)
        self.assertEqual(frame1_boxes[0].track_id, 1)
        self.assertFalse(frame1_boxes[0].is_tracked)
        
        # フレーム2：わずかに移動
        frame2_boxes = [
            BoundingBox(10, 10, 110, 110)
        ]
        self.assign_track_ids(frame1_boxes, frame2_boxes)
        self.assertEqual(frame2_boxes[0].track_id, 1)  # 同じIDを維持
        self.assertEqual(frame2_boxes[0].label, "eating")  # ラベルも継承
        self.assertTrue(frame2_boxes[0].is_tracked)
        
        # フレーム3：さらに移動
        frame3_boxes = [
            BoundingBox(20, 20, 120, 120)
        ]
        self.assign_track_ids(frame2_boxes, frame3_boxes)
        self.assertEqual(frame3_boxes[0].track_id, 1)  # まだ同じID
        self.assertEqual(frame3_boxes[0].label, "eating")
        self.assertTrue(frame3_boxes[0].is_tracked)
    
    def test_tracking_failure_new_id(self):
        """追跡失敗時の新規ID割り当てテスト"""
        # next_track_idをリセット
        self.next_track_id = 1
        
        # フレーム1
        frame1_boxes = [
            BoundingBox(0, 0, 100, 100, label="eating")
        ]
        self.assign_track_ids([], frame1_boxes)
        self.assertEqual(frame1_boxes[0].track_id, 1)
        
        # フレーム2：大きく移動してIOU < 0.4
        frame2_boxes = [
            BoundingBox(200, 200, 300, 300)
        ]
        self.assign_track_ids(frame1_boxes, frame2_boxes)
        self.assertEqual(frame2_boxes[0].track_id, 2)  # 新規ID
        self.assertIsNone(frame2_boxes[0].label)  # ラベルは継承されない
        self.assertFalse(frame2_boxes[0].is_tracked)
    
    def test_multiple_objects_tracking(self):
        """複数オブジェクトの追跡テスト"""
        # next_track_idをリセット
        self.next_track_id = 1
        
        # フレーム1：3頭の牛
        frame1_boxes = [
            BoundingBox(0, 0, 100, 100, label="eating"),
            BoundingBox(200, 0, 300, 100, label="standing"),
            BoundingBox(400, 0, 500, 100, label="walking")
        ]
        self.assign_track_ids([], frame1_boxes)
        
        # フレーム2：2頭が移動、1頭が消失、1頭が新規出現
        frame2_boxes = [
            BoundingBox(10, 10, 110, 110),  # ID:1 eating
            BoundingBox(410, 10, 510, 110),  # ID:3 walking
            BoundingBox(600, 600, 700, 700)  # 新規
        ]
        self.assign_track_ids(frame1_boxes, frame2_boxes)
        
        self.assertEqual(frame2_boxes[0].track_id, 1)
        self.assertEqual(frame2_boxes[0].label, "eating")
        self.assertEqual(frame2_boxes[1].track_id, 3)
        self.assertEqual(frame2_boxes[1].label, "walking")
        self.assertEqual(frame2_boxes[2].track_id, 4)  # 新規ID
        self.assertIsNone(frame2_boxes[2].label)
    
    def test_crossing_objects(self):
        """交差するオブジェクトの追跡テスト"""
        # next_track_idをリセット
        self.next_track_id = 1
        
        # フレーム1：2頭の牛が離れている
        frame1_boxes = [
            BoundingBox(0, 50, 100, 150, label="cow1"),
            BoundingBox(200, 50, 300, 150, label="cow2")
        ]
        self.assign_track_ids([], frame1_boxes)
        
        # ID割り当てを確認
        self.assertEqual(frame1_boxes[0].track_id, 1)
        self.assertEqual(frame1_boxes[1].track_id, 2)
        
        # フレーム2：交差に向かって移動（IOU >= 0.4を保証）
        frame2_boxes = [
            BoundingBox(40, 50, 140, 150),   # cow1が右へ（60%のオーバーラップ）
            BoundingBox(160, 50, 260, 150)   # cow2が左へ（60%のオーバーラップ）
        ]
        self.assign_track_ids(frame1_boxes, frame2_boxes)
        
        # ハンガリアンアルゴリズムによる最適マッチングを確認
        # frame2_boxes[0]とframe2_boxes[1]のIDの組み合わせが{1, 2}であることを確認
        track_ids = {frame2_boxes[0].track_id, frame2_boxes[1].track_id}
        self.assertEqual(track_ids, {1, 2})
        
        # 各ボックスが適切にマッチングされていることを確認
        # IOUが高い方とマッチングされているはず
        if frame2_boxes[0].track_id == 1:
            self.assertEqual(frame2_boxes[0].label, "cow1")
            self.assertEqual(frame2_boxes[1].track_id, 2)
            self.assertEqual(frame2_boxes[1].label, "cow2")
        else:
            self.assertEqual(frame2_boxes[0].track_id, 2)
            self.assertEqual(frame2_boxes[0].label, "cow2")
            self.assertEqual(frame2_boxes[1].track_id, 1)
            self.assertEqual(frame2_boxes[1].label, "cow1")


class TestTrackerIntegration(unittest.TestCase):
    """Trackerクラスの統合テスト（実装時用）"""
    
    def test_tracker_initialization(self):
        """Trackerクラスの初期化テスト"""
        # ここは実際のTrackerクラス実装後に記述
        pass
    
    def test_frame_to_frame_tracking(self):
        """フレーム間追跡の統合テスト"""
        # ここは実際のTrackerクラス実装後に記述
        pass
    
    def test_reset_tracking(self):
        """追跡リセット機能のテスト"""
        # ここは実際のTrackerクラス実装後に記述
        pass


if __name__ == '__main__':
    unittest.main()