#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会议室管理领域服务
提供会议室预订、可用性查询、时间冲突检测等功能
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from db.sqlite_repository import MeetingRoomRepository, MeetingRepository


class MeetingRoomStatus:
    """会议室状态常量"""
    AVAILABLE = "available"       # 可用
    BOOKED = "booked"              # 已预订
    MAINTENANCE = "maintenance"     # 维护中


class MeetingRoomService:
    """会议室管理服务"""
    
    @staticmethod
    def list_rooms(status: str = None) -> List[Dict[str, Any]]:
        """
        获取所有会议室列表
        
        Args:
            status: 可选的状态过滤 (available, booked, maintenance)
            
        Returns:
            会议室列表
        """
        return MeetingRoomRepository.get_all(status=status)
    
    @staticmethod
    def get_room(room_id: int) -> Optional[Dict[str, Any]]:
        """
        获取指定会议室详情
        
        Args:
            room_id: 会议室ID
            
        Returns:
            会议室信息或None
        """
        return MeetingRoomRepository.get_by_id(room_id)
    
    @staticmethod
    def create_room(name: str, capacity: int, location: str = None, 
                    status: str = MeetingRoomStatus.AVAILABLE) -> int:
        """
        创建新会议室
        
        Args:
            name: 会议室名称
            capacity: 容纳人数
            location: 位置
            status: 初始状态
            
        Returns:
            新创建的会议室ID
            
        Raises:
            ValueError: 参数验证失败
        """
        if not name or not name.strip():
            raise ValueError("会议室名称不能为空")
        if capacity <= 0:
            raise ValueError("容纳人数必须大于0")
        
        # 验证状态值
        valid_statuses = [MeetingRoomStatus.AVAILABLE, MeetingRoomStatus.BOOKED, MeetingRoomStatus.MAINTENANCE]
        if status not in valid_statuses:
            status = MeetingRoomStatus.AVAILABLE
        
        return MeetingRoomRepository.create(
            name=name.strip(),
            capacity=capacity,
            location=location,
            status=status
        )
    
    @staticmethod
    def update_room(room_id: int, **kwargs) -> bool:
        """
        更新会议室信息
        
        Args:
            room_id: 会议室ID
            **kwargs: 要更新的字段 (name, capacity, location, status)
            
        Returns:
            是否更新成功
        """
        # 验证状态值
        if "status" in kwargs:
            valid_statuses = [MeetingRoomStatus.AVAILABLE, MeetingRoomStatus.BOOKED, MeetingRoomStatus.MAINTENANCE]
            if kwargs["status"] not in valid_statuses:
                raise ValueError(f"无效的状态值: {kwargs['status']}")
        
        return MeetingRoomRepository.update(room_id, **kwargs)
    
    @staticmethod
    def delete_room(room_id: int) -> bool:
        """
        删除会议室
        
        Args:
            room_id: 会议室ID
            
        Returns:
            是否删除成功
        """
        return MeetingRoomRepository.delete(room_id)
    
    @staticmethod
    def set_maintenance(room_id: int) -> bool:
        """
        将会议室设为维护状态
        
        Args:
            room_id: 会议室ID
            
        Returns:
            是否设置成功
        """
        return MeetingRoomRepository.update(room_id, status=MeetingRoomStatus.MAINTENANCE)
    
    @staticmethod
    def set_available(room_id: int) -> bool:
        """
        将会议室设为可用状态
        
        Args:
            room_id: 会议室ID
            
        Returns:
            是否设置成功
        """
        return MeetingRoomRepository.update(room_id, status=MeetingRoomStatus.AVAILABLE)


class BookingService:
    """会议室预订服务"""
    
    @staticmethod
    def check_availability(room_id: int, start_time: str, end_time: str) -> Dict[str, Any]:
        """
        检查会议室在指定时间段是否可用
        
        Args:
            room_id: 会议室ID
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            
        Returns:
            {
                "available": bool,
                "conflicts": List[Dict]  # 如果有冲突，返回冲突会议列表
            }
        """
        # 获取会议室信息
        room = MeetingRoomRepository.get_by_id(room_id)
        if not room:
            return {"available": False, "error": "会议室不存在"}
        
        # 检查会议室状态
        if room["status"] == MeetingRoomStatus.MAINTENANCE:
            return {"available": False, "error": "会议室正在维护中"}
        
        # 检查时间冲突
        conflicts = MeetingRepository.check_conflict(room_id, start_time, end_time)
        
        return {
            "available": len(conflicts) == 0,
            "conflicts": conflicts
        }
    
    @staticmethod
    def get_available_rooms(start_time: str, end_time: str, 
                           min_capacity: int = None) -> List[Dict[str, Any]]:
        """
        查询指定时间段的可用会议室
        
        Args:
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            min_capacity: 最小容纳人数（可选）
            
        Returns:
            可用会议室列表
        """
        # 获取所有可用状态的会议室
        all_rooms = MeetingRoomRepository.get_all(status=MeetingRoomStatus.AVAILABLE)
        
        available_rooms = []
        for room in all_rooms:
            # 检查容量
            if min_capacity and room["capacity"] < min_capacity:
                continue
            
            # 检查时间冲突
            conflicts = MeetingRepository.check_conflict(
                room["id"], start_time, end_time
            )
            
            if not conflicts:
                available_rooms.append(room)
        
        return available_rooms
    
    @staticmethod
    def book_room(title: str, host_id: int, meeting_room_id: int,
                  start_time: str, end_time: str, notes: str = None) -> Dict[str, Any]:
        """
        预订会议室
        
        Args:
            title: 会议标题
            host_id: 主持人ID
            meeting_room_id: 会议室ID
            start_time: 开始时间
            end_time: 结束时间
            notes: 备注
            
        Returns:
            {
                "success": bool,
                "meeting_id": int,  # 如果成功
                "error": str,        # 如果失败
                "conflicts": List    # 如果有冲突
            }
        """
        # 验证参数
        if not title or not title.strip():
            return {"success": False, "error": "会议标题不能为空"}
        if not host_id:
            return {"success": False, "error": "主持人ID不能为空"}
        
        # 检查会议室是否存在
        room = MeetingRoomRepository.get_by_id(meeting_room_id)
        if not room:
            return {"success": False, "error": "会议室不存在"}
        
        # 检查会议室是否在维护
        if room["status"] == MeetingRoomStatus.MAINTENANCE:
            return {"success": False, "error": "会议室正在维护中"}
        
        # 检查时间冲突
        conflicts = MeetingRepository.check_conflict(meeting_room_id, start_time, end_time)
        if conflicts:
            return {
                "success": False,
                "error": "会议室在该时间段已被占用",
                "conflicts": conflicts
            }
        
        # 创建会议
        meeting_id = MeetingRepository.create(
            title=title.strip(),
            host_id=host_id,
            start_time=start_time,
            end_time=end_time,
            meeting_room_id=meeting_room_id,
            notes=notes,
            status="scheduled"
        )
        
        # 更新会议室状态为已预订
        MeetingRoomRepository.update(meeting_room_id, status=MeetingRoomStatus.BOOKED)
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "message": "会议室预订成功"
        }
    
    @staticmethod
    def cancel_booking(meeting_id: int) -> bool:
        """
        取消会议预订
        
        Args:
            meeting_id: 会议ID
            
        Returns:
            是否取消成功
        """
        # 获取会议信息
        meeting = MeetingRepository.get_by_id(meeting_id)
        if not meeting:
            return False
        
        # 软删除：将状态设为cancelled
        success = MeetingRepository.update(meeting_id, status="cancelled")
        
        # 如果会议关联了会议室，检查是否需要释放
        if success and meeting.get("meeting_room_id"):
            room_id = meeting["meeting_room_id"]
            
            # 检查该会议室是否还有其他未取消的会议
            remaining_meetings = MeetingRepository.get_all(
                status="scheduled"
            )
            has_active = any(
                m.get("meeting_room_id") == room_id and m["id"] != meeting_id
                for m in remaining_meetings
            )
            
            # 如果没有其他活动会议，释放会议室
            if not has_active:
                MeetingRoomRepository.update(room_id, status=MeetingRoomStatus.AVAILABLE)
        
        return success
    
    @staticmethod
    def get_room_bookings(room_id: int, date: str = None) -> List[Dict[str, Any]]:
        """
        获取会议室的预订记录
        
        Args:
            room_id: 会议室ID
            date: 日期 (YYYY-MM-DD格式，可选)
            
        Returns:
            预订记录列表
        """
        meetings = MeetingRepository.get_all(status="scheduled")
        
        # 过滤指定会议室的会议
        room_meetings = [
            m for m in meetings 
            if m.get("meeting_room_id") == room_id
        ]
        
        # 如果指定了日期，进一步过滤
        if date:
            room_meetings = [
                m for m in room_meetings
                if m.get("start_time", "").startswith(date)
            ]
        
        return room_meetings


def get_availability(date: str = None) -> Dict[str, Any]:
    """
    获取会议室可用性概览
    
    Args:
        date: 日期 (YYYY-MM-DD格式，默认今天)
        
    Returns:
        各会议室的可用性信息
    """
    from datetime import datetime
    
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # 获取所有会议室
    all_rooms = MeetingRoomRepository.get_all()
    
    availability = []
    for room in all_rooms:
        # 获取当天该会议室的预订
        bookings = BookingService.get_room_bookings(room["id"], date)
        
        availability.append({
            "room_id": room["id"],
            "room_name": room["name"],
            "capacity": room["capacity"],
            "location": room["location"],
            "status": room["status"],
            "bookings": [
                {
                    "meeting_id": b["id"],
                    "title": b["title"],
                    "start_time": b["start_time"],
                    "end_time": b["end_time"]
                }
                for b in bookings
            ]
        })
    
    return {
        "date": date,
        "rooms": availability
    }
