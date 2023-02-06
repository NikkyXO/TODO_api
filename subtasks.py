from flask import request, jsonify
from database import SessionLocal
from models import User, Task, Subtask, AssignedTasks
from flask_api import status
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required
from dateutil.parser import parse
from flask_json import json_response

db = SessionLocal()


def create_subtask():
    """
        It takes in a request and input data, validates the input data
        and creates a new subtask
        :request body input_data: The data that is passed to the function
        :return: A dictionary of new subtask
    """

    content = request.form["content"]
    due_date = request.form["due_date"]
    username = request.form["username"]
    due_date = parse(due_date)

    subtask_title = request.form["subtask_title"]
    task_name = request.form["task_name"]

    try:
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
                              content=content)
        db.add(new_subtask)
        db.commit()
        db.refresh(new_subtask)

        task.subtasks.append(new_subtask)
        db.add(task)
        db.commit()

        return jsonify(new_subtassk=new_subtask.to_json()), status.HTTP_200_OK

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e), error=e), status.HTTP_400_BAD_REQUEST


# revise endpoint with updates

def update_subtask():
    """
        It takes in a request and input data, validates the input data
        and updates a subtask
        :request body input_data: The data that is passed to the function
        :return: A dictionary of updated subtask
    """

    new_content = request.form["new_content"]
    new_due_date = request.form["new_due_date"]

    new_due_date = parse(new_due_date)

    old_subtask_title = request.form["old_subtask_title"]
    new_subtask_title = request.form["new_subtask_title"]
    task_name = request.form["task_name"]
    username = request.form["username"]

    try:

        user_account = db.query(User).filter(User.username == username).first()
        user_task = db.query(Task).filter(Task.task_name == task_name, Task.user_id == user_account.id).first()
        if user_task and user_account:

            user_subtask = db.query(Subtask).filter(Subtask.title == old_subtask_title,
                                                    Subtask.task_id == user_task.id,
                                                    Subtask.user_id == user_account.id).first()
            if user_subtask:
                user_subtask.content = new_content
                user_subtask.title = new_subtask_title
                user_subtask.due_date = new_due_date
                db.add(user_subtask)
                db.commit()
                db.refresh(user_subtask)

                # updates subtasks list in Task object
                subtasks = [subtask if subtask.id != user_subtask.id else user_subtask for subtask in
                            user_task.subtasks]
                user_task.subtasks = subtasks

                db.add(user_task)
                db.commit()
                return jsonify(new_subtask=user_subtask.to_json())
        return jsonify({'message': 'Task or user not found'}), status.HTTP_404_NOT_FOUND

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def get_subtask(username, task_name, subtask_title):
    """
        It takes request and parameters and gets
        the subtask for a  specific task
        :param task_name: The name of the task
        :param username: The name of the user
        :param subtask_title: The title of the sub-task
        :return: A json format of  subtask.
    """

    try:
        user = db.query(User).filter(User.username == username).first()
        task = db.query(Task).filter(Task.task_name == task_name).first()
        if user and task:
            get_user_subtask = db.query(Subtask).filter(Subtask.task_id == task.id,
                                                        Subtask.user_id == user.id,
                                                        Subtask.title == subtask_title).first()
            if get_user_subtask:
                return jsonify(subtasks=get_user_subtask.to_json()), status.HTTP_200_OK
            return jsonify(message="Subtask doesnt exist"), status.HTTP_404_NOT_FOUND

        return jsonify(message="user or subtask not found")

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


# REVISE
# Endpoint lags
def get_all_subtasks(username, task_name):
    """
        It takes request and parameters and gets all
        the subtask for a task
        :param task_name: The name of the task
        :param username: The name of the user
        :return: A json format of  all subtasks.
    """

    user = db.query(User).filter(User.username == username).first()

    task = db.query(Task).filter(Task.task_name == task_name).first()

    if user and task:

        subtasks = db.query(Subtask).filter(Subtask.task_id == task.id).all()
        if subtasks:
            all_subtasks = [sub.to_json() for sub in subtasks]
            #  _all_subtasks = json.dumps(subtasks, indent=4, cls=CustomEncoder)

            return json_response(message=all_subtasks), status.HTTP_200_OK
        return json_response(error="Subtasks not found"), status.HTTP_404_NOT_FOUND

    return jsonify(msg="No user or subtask "), status.HTTP_404_NOT_FOUND


def delete_subtask(username, task_name, subtask_title):
    """
        It takes request and parameters and deletes
        the subtask for a  specific task
        :param task_name: The name of the task
        :param username: The name of the user
        :param subtask_title: The title of the subtask
        :return: A Response Object.
    """

    user = db.query(User).filter(User.username == username).first()
    task = db.query(Task).filter(Task.task_name == task_name).first()
    if user and task:
        get_user_subtask = db.query(Subtask).filter(Subtask.task_id == task.id,
                                                    Subtask.user_id == user.id,
                                                    Subtask.title == subtask_title).first()
        if get_user_subtask:
            db.delete(get_user_subtask)
            db.commit()
            return jsonify(message="Subtask has been deleted"), status.HTTP_200_OK
        else:
            return jsonify(message="No subtask exist"), status.HTTP_404_NOT_FOUND

    return jsonify(message=f"No user or subtask found"), status.HTTP_404_NOT_FOUND


# revise this, double-same field

def assign_subtask(assign_to, task_name, subtask_title):
    """
        It takes request and parameters and assigns
        the subtask for a task
        :param assign_to: The name of the user to be assigned subtask
        :param task_name: The name of the task
        :param subtask_title: The title of the subtask
        :return: A Response Object.
    """

    try:
        task = db.query(Task).filter(Task.task_name == task_name).first()
        assignee_exists = db.query(User).filter(User.username == assign_to).first()
        print("task--->", task)
        print("assignee_exists:", assignee_exists)
        if task and assignee_exists:
            subtask = db.query(Subtask).filter(Subtask.task_id == task.id,
                                               Subtask.title == subtask_title).first()

            if not subtask:
                return jsonify(message=f"No subtask with title '{subtask_title}' "), status.HTTP_404_NOT_FOUND

            been_assigned = db.query(AssignedTasks).filter(AssignedTasks.subtask_id == subtask.id).first()
            if been_assigned:
                return jsonify(
                    message=f"Task: {subtask_title}, has been previously assigned "), \
                    status.HTTP_400_BAD_REQUEST

            task_to_assign = AssignedTasks(user_id=assignee_exists.id,
                                           subtask_id=subtask.id,
                                           task_id=task.id
                                           )
            db.add(task_to_assign)
            db.commit()

            subtask.assigned_to = assignee_exists.username
            db.add(subtask)
            db.commit()
            db.refresh(subtask)

            task.assigned_users.append(assignee_exists)
            # task.subtasks.append(subtask)
            db.add(task)
            db.commit()
            return jsonify({'message': 'subtask assigned to user'}), status.HTTP_200_OK
        return jsonify({'message': 'Task or User not found'}), status.HTTP_404_NOT_FOUND

    except IntegrityError as e:
        db.rollback()
        return jsonify(message="Task has been previously assigned to user"), status.HTTP_400_BAD_REQUEST


def unassign_subtask(unassign_from, task_name, subtask_title):
    """
        It takes request and parameters and unassigns
        the subtask
        :param unassign_from: The name of the user to be unassigned subtask
        :param task_name: The name of the task
        :param subtask_title: The title of the subtask
        :return: A Response Object.
    """
    try:
        task = db.query(Task).filter(Task.task_name == task_name).first()
        assigned = db.query(User).filter(User.username == unassign_from).first()
        if not task or not assigned:
            return jsonify({'message': 'Task or User not found'}), status.HTTP_404_NOT_FOUND

        subtask = db.query(Subtask).filter(Subtask.task == task,
                                           Subtask.title == subtask_title,
                                           Subtask.task_id == task.id,
                                           Subtask.assigned_to == assigned.username).first()

        if subtask:
            prev_assigned_subtask = db.query(AssignedTasks) \
                .filter(AssignedTasks.user_id == assigned.id,
                        AssignedTasks.task_id == task.id,
                        AssignedTasks.subtask_id == subtask.id
                        ).first()

            db.delete(prev_assigned_subtask)
            db.commit()

            subtask.assigned_to = None
            db.add(subtask)
            db.commit()
            db.refresh(subtask)

            if assigned in task.assigned_users:
                task.assigned_users.remove(assigned)
                # task.subtasks.update({subtask})
                db.add(task)
            db.commit()
            return jsonify({'message': 'subtask unassigned from user'}), status.HTTP_200_OK
        else:
            return jsonify(error="subtask not found"), status.HTTP_404_NOT_FOUND
    except IntegrityError as e:
        db.rollback()
        return jsonify(message="Task already not assigned to user"), status.HTTP_400_BAD_REQUEST


# EditStatus
def update_subtask_status():
    """
        It takes in a request and input data, validates the input data
        and updates a subtask status
        :request body input_data: The data that is passed to the function
        :return: A dictionary of updated subtask
    """
    username = request.form['username']
    task_name = request.form['task_name']
    subtask_title = request.form['subtask_title']
    _status = request.form['_status']
    user = db.query(User).filter(User.username == username).first()
    task = db.query(Task).filter(Task.task_name == task_name, Task.user_id == user.id).first()
    sub_task = db.query(Subtask).filter(Subtask.title == subtask_title,
                                        Subtask.task_id == task.id).first()

    if sub_task:
        sub_task.status = _status

        db.add(sub_task)
        db.commit()
        db.refresh(sub_task)

        task.subtasks.append = sub_task
        db.add(task)
        db.commit()

        return json_response(message="status updated successfully",
                             subtask=sub_task.to_json()), status.HTTP_201_CREATED
    return jsonify(error="Subtask not found"), status.HTTP_404_NOT_FOUND



# Retrieves assigned users for subtasks
def show_assigned_users_for_subtask(task_name, subtask_title):
    """
        It takes request and parameters and retrieves
        all assigned subtask
        :param task_name: The name of the task
        :param subtask_title: The title of the subtask
        :return: A Response Object.
    """
    task = db.query(Task).filter(Task.task_name == task_name).first()
    subtask_assigned = db.query(Subtask).filter(Subtask.task_id == task.id,
                                                Subtask.title == subtask_title).first()

    if task and subtask_assigned:
        get_subtask_assigned = db.query(AssignedTasks).filter(AssignedTasks.subtask_id == subtask_assigned.id).all()
        if not get_subtask_assigned:
            return jsonify(message="No subtasks assigned in task")

        get_sub_tasks = [sub_task.to_json() for sub_task in get_subtask_assigned]

        return jsonify(subtitle_name=subtask_title,
                       task_name=task_name,
                       assigned_subtasks=get_sub_tasks,
                       assigned_to=subtask_assigned.assigned_to), status.HTTP_200_OK

    return jsonify(message=f"No assigned user found for{subtask_title} in {task_name}"), status.HTTP_404_NOT_FOUND
