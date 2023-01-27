from flask import request, jsonify
from database import SessionLocal
from models import User, Task, Subtask, assigned_tasks
from flask_api import status
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required

db = SessionLocal()


@jwt_required()
def create_task():
    username = request.form["username"]
    task_name = request.form["task_name"]
    title = request.form["title"]

    get_user_account = db.query(User).filter(User.username == username).first()
    if not get_user_account:
        return {"message": "Account doesnt exist."}, status.HTTP_400_BAD_REQUEST

    user_task = Task(
        user_id=get_user_account.id,
        title=title,
        task_name=task_name
    )

    db.add(user_task)
    db.commit()
    db.refresh(user_task)


@jwt_required()
def get_task(username, task_name):
    get_user = db.query(User).filter(User.username == username).first()
    get_user_task = db.query(Task).filter(Task.task_name == task_name,
                                          Task.user_id == get_user.id).first()
    if get_user_task:
        return jsonify(task=get_user_task.to_json()), status.HTTP_200_OK
    return jsonify(message=f"No task found for {username}")


@jwt_required()
def get_all_tasks(username):
    get_user = db.query(User).filter(User.username == username).first()


    if get_user:
        user_tasks = db.query(Task).filter(Task.user_id == get_user.id).all()
        all_tasks = [task.to_json() for task in user_tasks]

        return jsonify(task=all_tasks), 200
    return jsonify(message="No tasks found for user")


@jwt_required()
def update_task():
    old_title = request.form["old_title"]
    new_title = request.form["new_title"]
    old_task_name = request.form["old_task_name"]
    new_task_name = request.form["new_task_name"]

    get_user_task = db.query(Task).filter(Task.task_name == old_task_name,
                                          Task.title == old_title).first()
    if get_user_task:
        get_user_task.task_name = new_task_name
        get_user_task.title = new_title

        db.add(get_user_task)
        db.commit()
        db.refresh(get_user_task)
        return jsonify(user_task=get_user_task.to_json())
    return jsonify(message="No Task for {old_task_name}")


@jwt_required()
def delete_task(username, task_name):
    get_user = db.query(User).filter(User.username == username).first()
    get_user_task = db.query(Task).filter(Task.task_name == task_name).first()
    if get_user_task:
        db.delete(get_user_task)
        db.commit()

        db.add(get_user)
        db.commit()

        return jsonify(task="Task has been successfully deleted"), 200
    return jsonify(message=f"No task found for {task_name}"), status.HTTP_404_NOT_FOUND


@jwt_required()
def clear_all_user_tasks(username):
    get_user = db.query(User).filter(User.username == username).first()
    if get_user:
        # gets all tasks associated with the user

        get_task_objs = db.query(Task).filter(Task.user_id == get_user.id).all()

        # gets all subtask associated with the tasks in Task Table and delete them
        for task in get_task_objs:
            db.delete(task.subtasks)

        # gets all subtasks instances associated user tasks in Subtask table  them
        get_subtask_objs = db.query(Subtask).filter(Subtask.user_id == get_user.id).all()

        # deletes all tasks and associated subtasks
        db.expunge_all(get_task_objs)
        db.expunge_all(get_subtask_objs)
        db.commit()

    return jsonify(message=f"User {username} not found")


@jwt_required()
def assign_task(assign_to, task_name):
    try:
        task = db.query(Task).filter(Task.name == task_name).first()

        # checks if assignee is also a user
        assignee = db.query(User).filter(User.username == assign_to).first()
        if not task or not assignee:
            return jsonify({'message': 'Task or User not found'}), 404

        task_to_assign = assigned_tasks(user_id=assignee.id,
                                        task_id=task.id
                                        )
        db.add(task_to_assign)
        db.commit()

        task.assigned_users.append(assignee)
        assignee.assigned_tasks.append(task)
        db.add(task)
        db.add(assignee)
        db.commit()
        return jsonify({'message': 'Task assigned to user'}), 200

    except IntegrityError as e:
        db.rollback()
        return jsonify(message="Task already assigned to user",
                       error=e), 400


@jwt_required()
def unassign_task(unassigned_from, task_name):
    try:
        task = db.query(Task).filter(Task.name == task_name).first()
        assignee = db.query(User).filter(User.username == unassigned_from).first()

        tasks_assigned_before = db.query(assigned_tasks).filter(assigned_tasks.user_id ==
                                                                assignee.id,
                                                                assigned_tasks.task_id == task.id).all()
        if not task or not assignee:
            return jsonify({'message': 'Task or assigned user not found'}), 404

        # querying all the rows in the assigned_tasks table where the
        # user_id is equal to the id of the user  to unassign
        for task in tasks_assigned_before:
            db.query(assigned_tasks).filter(
                assigned_tasks.user_id == assignee.id) \
                .update({"user_id": None})

        # also remove task from assigned_tasks list in Users table
        # and remove user from assigned_users list in  tasks table
        task.assigned_users.remove(assignee)
        assignee.assigned_tasks.remove(task)
        db.add(task)
        db.add(assignee)
        db.commit()
        return jsonify({'message': 'Task unassigned from user'}), 200

    except IntegrityError as e:
        db.rollback()
        return jsonify(message="Task previously not assigned to user"), 400
