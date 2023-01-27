from flask import request, jsonify
from database import SessionLocal
from models import User, Task, Subtask, assigned_tasks
from flask_api import status
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required
from dateutil.parser import parse

db = SessionLocal()


# status
# - username
# - task_name
# - subtask_title
# - due_date
# content
@jwt_required()
def create_subtask():
    content = request.form["content"]
    due_date = request.form["due_date"]
    due_date = parse(due_date)
    _status = request.form["status"]
    subtask_title = request.form["subtask_title"]
    task_name = request.form["task_name"]
    username = request.form["username"]

    task = db.query(Task).filter(Task.task_name == task_name).first()
    user = db.query(User).filter(User.username == username).first()

    if not task:
        return jsonify({'message': 'Task or user not found'}), 404

    elif not user:
        return jsonify({'message': 'Task or user not found'}), 404
    new_subtask = Subtask(task=task,
                          task_id=task.id,
                          user_id=user.id,
                          due_date=due_date,
                          title=subtask_title,
                          content=content,
                          status=_status)
    db.add(new_subtask)
    db.commit()
    db.refresh(new_subtask)

    task.subtasks.append(new_subtask)
    db.add(task)
    db.commit()

    return jsonify(new_subtassk=new_subtask.to_json()), status.HTTP_200_OK


# revise endpoint with updates
@jwt_required()
def update_subtask():
    new_content = request.form["new_content"]
    new_due_date = request.form["new_due_date"]

    new_due_date = parse(new_due_date)

    new_status = request.form["new_status"]
    old_subtask_title = request.form["old_subtask_title"]
    new_subtask_title = request.form["new_subtask_title"]
    task_name = request.form["task_name"]
    username = request.form["username"]

    user_task = db.query(Task).filter(Task.task_name == task_name).first()
    user_account = db.query(User).filter(User.username == username).first()
    if not user_task or user_account:
        return jsonify({'message': 'Task or user not found'}), status.HTTP_404_NOT_FOUND

    user_subtask = db.query(Subtask).filter(Subtask.title == old_subtask_title,
                                            Subtask.task_id == user_task.id,
                                            Subtask.user_id == user_account).first()

    user_subtask.content = new_content
    user_subtask.status = new_status
    user_subtask.title = new_subtask_title
    user_subtask.due_date = new_due_date
    db.add(user_subtask)
    db.commit()
    db.refresh(user_subtask)

    for subtask in user_task.subtasks:
        if subtask.id == user_subtask.id:
            user_task.subtasks.update(user_subtask)
            break

    db.add(user_task)
    db.commit()
    return jsonify(new_subtask=user_subtask.to_json())


@jwt_required()
def get_subtask(username, task_name, subtask_title):
    user = db.query(User).filter(User.username == username).first()
    task = db.query(Task).filter(Task.task_name == task_name).first()
    if user and task:
        get_user_subtask = db.query(Subtask).filter(Subtask.task_id == task.id,
                                                    Subtask.user_id == user.id,
                                                    Subtask.title == subtask_title).first()

        return jsonify(subtasks=get_user_subtask.to_json()), status.HTTP_200_OK

    return jsonify(message="user or subtask not found")


@jwt_required()
def get_all_subtasks(username, task_name):  # added extra param
    user = db.query(User).filter(User.username == username).first()
    get_user_tasks = db.query(Task).filter(Task.user_id == user.id,
                                           Task.task_name == task_name).all()
    if user and get_user_tasks:
        list_subtasks = []
        for task in get_user_tasks:
            for sub in task:
                list_subtasks.apend(sub.subtasks.to_json())

        return jsonify(subtasks=list_subtasks), status.HTTP_200_OK

    return jsonify(message=f"No user or subtask for {username}"), status.HTTP_404_NOT_FOUND


@jwt_required()
def delete_subtask(username, task_name, subtask_title):
    user = db.query(User).filter(User.username == username).first()
    task = db.query(Task).filter(Task.name == task_name).first()
    if user and task:
        get_user_subtask = db.query(Subtask).filter(Subtask.task_id == task.id,
                                                    Subtask.user_id == user.id,
                                                    Subtask.title == subtask_title).first()

        db.delete(get_user_subtask)
        db.commit()
        task.subtasks.remove(get_user_subtask)
        db.commit()
        return jsonify(message="Subtask has been deleted"), status.HTTP_200_OK

    return jsonify(message=f"No user or subtask for {username}"), status.HTTP_404_NOT_FOUND


# revise this, double-same field
@jwt_required()
def assign_subtask(assign_to, task_name, subtask_title):
    try:
        task = db.query(Task).filter(Task.name == task_name).first()
        assignee = db.query(User).filter(User.username == assign_to).first()
        if not task or not assignee:
            return jsonify({'message': 'Task or User not found'}), status.HTTP_404_NOT_FOUND

        subtask = db.query(Subtask).filter(Subtask.task == task,
                                           Subtask.title == subtask_title).first()

        task_to_assign = assigned_tasks(user_id=assignee.id,
                                        task_id=task.id,
                                        subtask_id=subtask.id
                                        )
        db.add(task_to_assign)
        db.commit()

        subtask.assigned_to = assignee
        db.add(subtask)
        db.commit()
        db.refresh(subtask)

        task.assigned_users.append(assignee)
        task.subtasks.update({subtask})
        db.add(task)
        db.commit()
        return jsonify({'message': 'subtask assigned to user'}), status.HTTP_200_OK

    except IntegrityError as e:
        db.rollback()
        return jsonify(message="Task already assigned to user"), status.HTTP_400_BAD_REQUEST


@jwt_required()
def unassign_subtask(unassign_from, task_name, subtask_title):
    try:
        task = db.query(Task).filter(Task.name == task_name).first()
        assigned = db.query(User).filter(User.username == unassign_from).first()
        if not task or not assigned:
            return jsonify({'message': 'Task or User not found'}), status.HTTP_404_NOT_FOUND

        subtask = db.query(Subtask).filter(Subtask.task == task,
                                           Subtask.title == subtask_title,
                                           Subtask.assigned_to == assigned).first()

        prev_assigned_subtask = db.query(assigned_tasks) \
            .filter(assigned_tasks.user_id == assigned.id,
                    assigned_tasks.subtasks_id == subtask.id
                    ).first()

        db.delete(prev_assigned_subtask)
        db.commit()

        subtask.assigned_to = None
        db.add(subtask)
        db.commit()
        db.refresh(subtask)

        task.assigned_users.remove(assigned)
        task.subtasks.update({subtask})
        db.add(task)
        db.commit()
        return jsonify({'message': 'subtask unassigned from user'}), status.HTTP_200_OK

    except IntegrityError as e:
        db.rollback()
        return jsonify(message="Task already not assigned to user"), status.HTTP_400_BAD_REQUEST


# Endpoint not necessary
@jwt_required()
def get_all_subtasks_assignees(username,
                               task_name):  # This method will return the assignees of all subtasks for the task
    user = db.query(User).filter(User.username == username).first()
    task = db.query(Task).filter(Task.name == task_name, Task.user_id == user.id).first()

    assignees = [sub_task.assignee for sub_task in task.subtasks]

    return jsonify(assignees=assignees), status.HTTP_201_CREATED


# - username
# - old_title
# - new_title
# - old_task_name
# - new_task_name
@jwt_required()  # EditStatus
def update_subtask_status(username, task_name, subtask_title, _status):  # old task_name, old subtask_title
    user = db.query(User).filter(User.username == username).first()
    task = db.query(Task).filter(Task.name == task_name, Task.user_id == user.id).first()
    sub_task = db.query(Subtask).filter(Subtask.title == subtask_title,
                                        Subtask.task_id == task.id).first()
    sub_task.status = _status

    db.add(sub_task)
    db.commit()
    db.refresh(sub_task)

    task.subtasks.update(sub_task)
    db.add(task)
    db.commit()

    return jsonify(message="status updated successfully",
                   subtask=sub_task), status.HTTP_201_CREATED


@jwt_required()
def show_assigned_tasks(username):
    # Retrieve all assigned tasks from the database
    user_account = db.query(User).filter(User.username == username)
    tasks_assigned = db.query(Task).filter(Task.user_id == user_account.id, Task.assigned_users is not None).all()

    # Convert assigned tasks to a list of dictionaries for easy serialization
    task_list = [task.to_json() for task in tasks_assigned]

    # Return the list of assigned tasks in the response
    return jsonify(assigned_tasks=task_list), status.HTTP_200_OK


# view assigned users
def show_assigned_users(username, task_name):
    # Retrieve all assigned users from the database
    user_account = db.query(User).filter(User.username == username)
    task_assigned = db.query(Task).filter(Task.user_id == user_account.id,
                                          Task.task_name == task_name,
                                          Task.assigned_users is not None).first()

    if task_assigned:
        # Return the list of assigned users in task in the response
        return jsonify(assigned_tasks=task_assigned.assigned_users.to_json()), status.HTTP_200_OK

    return jsonify(message=f"No assigned user found for {task_name}"), status.HTTP_404_NOT_FOUND
