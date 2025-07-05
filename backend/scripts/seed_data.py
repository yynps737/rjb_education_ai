#!/usr/bin/env python3
"""
种子数据脚本 - 创建测试数据
"""
import sys
import os
from datetime import datetime, timedelta
import random

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models.database import engine, SessionLocal
from models.user import User, UserRole
from models.course import Course, Chapter, Lesson
from models.assignment import Assignment, Question, AssignmentStatus, QuestionType
from models.knowledge import KnowledgeDocument
from services.user_service import user_service
from utils.auth import get_password_hash
# from core.llm.embeddings import embedding_service  # 暂时注释，稍后处理向量存储
from core.vector_db.optimized_chroma_store import OptimizedChromaStore
import asyncio


class SeedData:
    def __init__(self):
        self.db = SessionLocal()
        self.vector_store = OptimizedChromaStore()
        
    def create_users(self):
        """创建测试用户"""
        print("创建测试用户...")
        
        users_data = [
            # 管理员
            {"username": "admin", "password": "admin123", "email": "admin@edu.com", 
             "full_name": "系统管理员", "role": UserRole.ADMIN},
            
            # 教师
            {"username": "teacher1", "password": "teacher123", "email": "teacher1@edu.com", 
             "full_name": "张老师", "role": UserRole.TEACHER},
            {"username": "teacher2", "password": "teacher123", "email": "teacher2@edu.com", 
             "full_name": "李老师", "role": UserRole.TEACHER},
            
            # 学生
            {"username": "student1", "password": "student123", "email": "student1@edu.com", 
             "full_name": "王小明", "role": UserRole.STUDENT},
            {"username": "student2", "password": "student123", "email": "student2@edu.com", 
             "full_name": "李小红", "role": UserRole.STUDENT},
            {"username": "student3", "password": "student123", "email": "student3@edu.com", 
             "full_name": "张小华", "role": UserRole.STUDENT},
        ]
        
        self.users = {}
        for user_data in users_data:
            # 检查用户是否已存在
            existing_user = self.db.query(User).filter(User.username == user_data["username"]).first()
            if existing_user:
                print(f"用户 {user_data['username']} 已存在，跳过")
                self.users[user_data["role"]] = self.users.get(user_data["role"], [])
                self.users[user_data["role"]].append(existing_user)
                continue
                
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                hashed_password=get_password_hash(user_data["password"])
            )
            self.db.add(user)
            
            # 按角色分组保存
            if user_data["role"] not in self.users:
                self.users[user_data["role"]] = []
            self.users[user_data["role"]].append(user)
            
            print(f"创建用户: {user_data['username']} ({user_data['role'].value})")
        
        self.db.commit()
        print(f"✓ 用户创建完成\n")
        
    def create_courses(self):
        """创建测试课程"""
        print("创建测试课程...")
        
        courses_data = [
            {
                "title": "Python程序设计基础",
                "description": "面向初学者的Python编程课程，从基础语法到实际应用",
                "subject": "计算机科学",
                "grade_level": "大学一年级",
                "teacher_idx": 0,
                "chapters": [
                    {
                        "title": "Python入门",
                        "order_num": 1,
                        "lessons": [
                            {"title": "Python简介与环境搭建", "content": "Python是一种解释型、面向对象的高级编程语言..."},
                            {"title": "基本数据类型", "content": "Python中的基本数据类型包括整数、浮点数、字符串..."},
                            {"title": "变量与运算符", "content": "变量是存储数据的容器，运算符用于执行各种操作..."}
                        ]
                    },
                    {
                        "title": "控制结构",
                        "order_num": 2,
                        "lessons": [
                            {"title": "条件语句", "content": "if-elif-else语句用于条件判断..."},
                            {"title": "循环语句", "content": "for循环和while循环的使用方法..."},
                            {"title": "函数定义", "content": "函数是组织好的、可重复使用的代码块..."}
                        ]
                    }
                ]
            },
            {
                "title": "数据结构与算法",
                "description": "计算机科学核心课程，学习常用数据结构和基础算法",
                "subject": "计算机科学",
                "grade_level": "大学二年级",
                "teacher_idx": 0,
                "chapters": [
                    {
                        "title": "线性数据结构",
                        "order_num": 1,
                        "lessons": [
                            {"title": "数组与链表", "content": "数组是连续存储的数据结构，链表是动态数据结构..."},
                            {"title": "栈与队列", "content": "栈遵循LIFO原则，队列遵循FIFO原则..."},
                        ]
                    }
                ]
            },
            {
                "title": "高等数学",
                "description": "大学数学基础课程，包括微积分、线性代数等内容",
                "subject": "数学",
                "grade_level": "大学一年级",
                "teacher_idx": 1,
                "chapters": [
                    {
                        "title": "函数与极限",
                        "order_num": 1,
                        "lessons": [
                            {"title": "函数的概念", "content": "函数是数学中的基本概念，表示变量之间的对应关系..."},
                            {"title": "极限的定义", "content": "极限是微积分的基础概念..."},
                        ]
                    }
                ]
            }
        ]
        
        self.courses = []
        for course_data in courses_data:
            # 检查课程是否已存在
            existing_course = self.db.query(Course).filter(Course.title == course_data["title"]).first()
            if existing_course:
                print(f"课程 {course_data['title']} 已存在，跳过")
                self.courses.append(existing_course)
                continue
                
            teacher = self.users[UserRole.TEACHER][course_data["teacher_idx"]]
            
            course = Course(
                title=course_data["title"],
                description=course_data["description"],
                subject=course_data["subject"],
                grade_level=course_data["grade_level"],
                teacher_id=teacher.id
            )
            self.db.add(course)
            self.db.flush()
            
            # 创建章节和课时
            for chapter_data in course_data["chapters"]:
                chapter = Chapter(
                    course_id=course.id,
                    title=chapter_data["title"],
                    order=chapter_data["order_num"]
                )
                self.db.add(chapter)
                self.db.flush()
                
                for idx, lesson_data in enumerate(chapter_data["lessons"]):
                    lesson = Lesson(
                        chapter_id=chapter.id,
                        title=lesson_data["title"],
                        content=lesson_data["content"],
                        order=idx + 1
                    )
                    self.db.add(lesson)
                    
            # 刷新以获取ID
            self.db.flush()
            
            # 随机分配学生到课程
            students = self.users.get(UserRole.STUDENT, [])
            for student in random.sample(students, min(len(students), random.randint(2, len(students)))):
                course.users.append(student)
            
            self.courses.append(course)
            print(f"创建课程: {course_data['title']} (教师: {teacher.full_name})")
        
        self.db.commit()
        print(f"✓ 课程创建完成\n")
        
    def create_assignments(self):
        """创建测试作业"""
        print("创建测试作业...")
        
        assignments_data = [
            {
                "course_idx": 0,  # Python课程
                "title": "Python基础练习",
                "description": "完成Python基础语法相关的练习题",
                "due_days": 7,
                "questions": [
                    {
                        "type": QuestionType.SINGLE_CHOICE,
                        "content": "Python中定义函数使用哪个关键字？",
                        "options": ["function", "def", "define", "func"],
                        "answer": "1",  # 索引1对应 "def"
                        "points": 5
                    },
                    {
                        "type": QuestionType.MULTIPLE_CHOICE,
                        "content": "以下哪些是Python的内置数据类型？",
                        "options": ["list", "array", "dict", "struct"],
                        "answer": "0,2",  # list和dict
                        "points": 10
                    },
                    {
                        "type": QuestionType.TRUE_FALSE,
                        "content": "Python是一种编译型语言。",
                        "answer": "false",
                        "points": 5
                    },
                    {
                        "type": QuestionType.SHORT_ANSWER,
                        "content": "简述Python中列表(list)和元组(tuple)的区别。",
                        "answer": "列表是可变的，元组是不可变的",
                        "points": 15
                    }
                ]
            },
            {
                "course_idx": 0,  # Python课程
                "title": "函数与模块作业",
                "description": "练习函数定义和模块使用",
                "due_days": 10,
                "questions": [
                    {
                        "type": QuestionType.CODING,
                        "content": "编写一个函数，计算斐波那契数列的第n项。",
                        "answer": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                        "points": 20
                    }
                ]
            },
            {
                "course_idx": 2,  # 高等数学课程
                "title": "极限计算练习",
                "description": "完成极限相关的计算题",
                "due_days": 5,
                "questions": [
                    {
                        "type": QuestionType.SHORT_ANSWER,
                        "content": "计算极限：lim(x→0) sin(x)/x，请写出计算过程",
                        "answer": "1",
                        "points": 10
                    }
                ]
            }
        ]
        
        self.assignments = []
        for assign_data in assignments_data:
            course = self.courses[assign_data["course_idx"]]
            
            # 检查作业是否已存在
            existing = self.db.query(Assignment).filter(
                Assignment.course_id == course.id,
                Assignment.title == assign_data["title"]
            ).first()
            if existing:
                print(f"作业 {assign_data['title']} 已存在，跳过")
                continue
            
            assignment = Assignment(
                course_id=course.id,
                title=assign_data["title"],
                description=assign_data["description"],
                due_date=datetime.now() + timedelta(days=assign_data["due_days"]),
                total_points=sum(q["points"] for q in assign_data["questions"]),
                status=AssignmentStatus.PUBLISHED
            )
            self.db.add(assignment)
            self.db.flush()
            
            # 创建题目
            for idx, q_data in enumerate(assign_data["questions"]):
                question = Question(
                    assignment_id=assignment.id,
                    question_type=q_data["type"],
                    content=q_data["content"],
                    options=q_data.get("options"),
                    correct_answer=q_data["answer"],
                    points=q_data["points"],
                    order=idx + 1
                )
                self.db.add(question)
            
            self.assignments.append(assignment)
            print(f"创建作业: {assign_data['title']} (课程: {course.title})")
        
        self.db.commit()
        print(f"✓ 作业创建完成\n")
        
    def create_knowledge_base(self):
        """创建知识库内容"""
        print("创建知识库内容...")
        
        # 创建临时文件夹存储知识文档
        import tempfile
        import pathlib
        
        # 使用项目的临时文件夹
        temp_dir = pathlib.Path("/home/kkb/RJB/backend/temp_knowledge_docs")
        temp_dir.mkdir(exist_ok=True)
        
        knowledge_data = [
            {
                "course_idx": 0,  # Python课程
                "title": "Python编程基础知识",
                "content": """
# Python编程基础

## 1. Python简介
Python是一种高级编程语言，具有简洁易读的语法。它支持多种编程范式，包括面向对象、函数式和过程式编程。

## 2. 基本数据类型
- 整数(int): 如 1, 2, 3
- 浮点数(float): 如 3.14, 2.718
- 字符串(str): 如 "Hello", 'World'
- 布尔值(bool): True 或 False
- 列表(list): 如 [1, 2, 3]
- 字典(dict): 如 {"name": "Python", "version": 3.9}

## 3. 控制流
### 条件语句
```python
if condition:
    # 执行代码
elif another_condition:
    # 执行其他代码
else:
    # 默认执行
```

### 循环语句
```python
# for循环
for i in range(10):
    print(i)

# while循环
while condition:
    # 执行代码
```

## 4. 函数定义
```python
def function_name(parameters):
    '''函数文档字符串'''
    # 函数体
    return result
```
                """,
                "file_type": "md"
            },
            {
                "course_idx": 1,  # 数据结构课程
                "title": "数据结构基础概念",
                "content": """
# 数据结构基础

## 1. 数组（Array）
数组是相同类型元素的集合，存储在连续的内存空间中。
- 优点：随机访问快，时间复杂度O(1)
- 缺点：插入删除慢，大小固定

## 2. 链表（Linked List）
链表由节点组成，每个节点包含数据和指向下一个节点的指针。
- 优点：插入删除快，大小动态
- 缺点：随机访问慢，需要额外空间存储指针

## 3. 栈（Stack）
栈是一种后进先出(LIFO)的数据结构。
- 主要操作：push（入栈）、pop（出栈）、peek（查看栈顶）
- 应用：函数调用、表达式求值、括号匹配

## 4. 队列（Queue）
队列是一种先进先出(FIFO)的数据结构。
- 主要操作：enqueue（入队）、dequeue（出队）
- 应用：任务调度、消息队列、广度优先搜索
                """,
                "file_type": "md"
            }
        ]
        
        for doc_data in knowledge_data:
            course = self.courses[doc_data["course_idx"]]
            teacher = self.users[UserRole.TEACHER][0]  # 使用第一个教师作为上传者
            
            # 检查文档是否已存在
            existing = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.course_id == course.id,
                KnowledgeDocument.title == doc_data["title"]
            ).first()
            if existing:
                print(f"知识文档 {doc_data['title']} 已存在，跳过")
                continue
            
            # 创建文件
            file_name = f"{doc_data['title'].replace(' ', '_')}.{doc_data['file_type']}"
            file_path = temp_dir / file_name
            
            # 写入内容到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc_data["content"])
            
            # 创建文档记录
            doc = KnowledgeDocument(
                course_id=course.id,
                title=doc_data["title"],
                file_path=str(file_path),
                file_type=doc_data["file_type"],
                file_size=len(doc_data["content"].encode('utf-8')),
                uploaded_by=teacher.id
            )
            self.db.add(doc)
            
            print(f"创建知识文档: {doc_data['title']} (课程: {course.title})")
        
        self.db.commit()
        print(f"✓ 知识库创建完成\n")
    
    def _split_content(self, content: str, chunk_size: int = 500) -> list:
        """将内容分块"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()


def main():
    """主函数"""
    print("=== 开始创建种子数据 ===\n")
    
    seeder = SeedData()
    
    try:
        # 创建基础数据
        seeder.create_users()
        seeder.create_courses()
        seeder.create_assignments()
        
        # 创建知识库 - 暂时跳过，因为需要实际文件处理
        # seeder.create_knowledge_base()
        print("\n提示: 知识库创建已跳过，需要时可手动上传文档")
        
        print("\n=== 种子数据创建完成 ===")
        print("\n测试账号信息：")
        print("管理员 - 用户名: admin, 密码: admin123")
        print("教师 - 用户名: teacher1, 密码: teacher123")
        print("学生 - 用户名: student1, 密码: student123")
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        seeder.close()


if __name__ == "__main__":
    main()