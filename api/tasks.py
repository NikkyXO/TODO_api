from flask import request, jsonify
from settings.database import SessionLocal
from .models import User, Task, Subtask, AssignedTasks
from flask_api import status
from sqlalchemy.exc import IntegrityError
import sqlalchemy as sa

db = SessionLocal()


def create_task():
    """
        It takes in a request and input data, validates the input data
        and creates a new task
        :request body input_data: The data that is passed to the function
        :return: A dictionary of new task
    """

    task_name = request.form["task_name"]
    username = request.form["username"]
    title = request.form["title"]

    try:
        get_user_account = db.query(User).filter(User.username == username).first()
        if not get_user_account:
            return {"message": "Account doesnt exist."}, status.HTTP_400_BAD_REQUEST

        task_exists = db.query(Task).filter(Task.task_name == task_name).first()
        if task_exists:
            return jsonify(message="Task Already Exists"), status.HTTP_400_BAD_REQUEST

        user_task = Task(
            user_id=get_user_account.id,
            title=title,
            task_name=task_name
        )

        db.add(user_task)
        db.query(Task).group_by(sa.func.year(user_task.created_at), sa.func.month(Task.created_at))
        db.commit()

        db.refresh(user_task)

        return jsonify(message="Task created successfully", detail=user_task.to_dict())

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def get_task(username, task_name):
    """
        It takes request and parameters and gets
        the subtask for a  specific task
        :param task_name: The name of the task
        :param username: The name of the user
        :return: A json formatted response object of  task.
    """
    try:
        get_user = db.query(User).filter(User.username == username).first()
        if get_user:
            get_user_task = db.query(Task).filter(Task.task_name == task_name,
                                                  Task.user_id == get_user.id).first()
            if not get_user_task:
                return jsonify(error="Task doesnt exist"), status.HTTP_404_NOT_FOUND

            return jsonify(task=get_user_task.to_dict()), status.HTTP_200_OK

        return jsonify(error="User doesnt exist"), status.HTTP_404_NOT_FOUND

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def get_all_user_tasks(username):
    """
        It gets all the tasks for a user
        :param username: The name of the user
        :return: A json formatted response object of  all user tasks.
    """

    try:
        get_user = db.query(User).filter(User.username == username).first()

        if get_user:
            user_tasks = db.query(Task).filter(Task.user_id == get_user.id).all()
            all_tasks = [task.to_dict() for task in user_tasks]

            return jsonify(task=all_tasks), 200
        return jsonify(message="No tasks found for user")

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def get_all_tasks():
    """
        It gets all the tasks objects from the database
        :return: A json formatted response object of  all task objects
    """
    try:
        all_tasks = db.query(Task).all()
        if not all_tasks:
            return jsonify(error="No tasks found"), status.HTTP_404_NOT_FOUND

        tasks = [task.to_dict() for task in all_tasks]

        return jsonify(tasks=tasks)

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def update_task():
    """
        It takes in a request and input data, validates the input data
        and updates a task
        :request body input_data: The data that is passed to the function
        :return: A json formatted response of updated task
    """
    old_title = request.form["old_title"]
    new_title = request.form["new_title"]
    old_task_name = request.form["old_task_name"]
    new_task_name = request.form["new_task_name"]

    try:
        get_user_task = db.query(Task).filter(Task.task_name == old_task_name,
                                              Task.title == old_title).first()
        print("user_task--->", get_user_task)
        if get_user_task:
            get_user_task.task_name = new_task_name
            get_user_task.title = new_title

            db.add(get_user_task)
            db.commit()
            db.refresh(get_user_task)
            return jsonify(user_task=get_user_task.to_dict())
        return jsonify(message=f"No Task for {old_task_name}")

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def delete_task(username, task_name):
    """
        It takes request and parameters and deletes
        the task
        :param username: The name of the user
        :param task_name: The name of the task
        :return: A json formatted Response Object.
    """

    try:
        get_user = db.query(User).filter(User.username == username).first()
        get_user_task = db.query(Task).filter(Task.task_name == task_name).first()
        if get_user_task:
            db.delete(get_user_task)
            db.commit()

            db.add(get_user)
            db.commit()

            return jsonify(task="Task has been successfully deleted"), 200
        return jsonify(message=f"No task found for {task_name}"), status.HTTP_404_NOT_FOUND

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def clear_all_user_tasks(username):
    """
        It deletes all tasks for a user
        :param username: The name of the user
        :return: A Response Object.
    """
    try:
        get_user = db.query(User).filter(User.username == username).first()
        if get_user:
            # gets all tasks associated with the user
            get_task_objs = db.query(Task).filter(Task.user_id == get_user.id).all()

            # gets all subtask associated with the tasks in Task Table and delete them
            for task in get_task_objs:
                for subtask in task.subtasks:
                    db.delete(subtask)

            # gets all subtasks instances associated user tasks in Subtask table  them
            get_subtask_objs = db.query(Subtask).filter(Subtask.user_id == get_user.id).all()

            # deletes all tasks and associated subtasks
            for task in get_task_objs:
                db.delete(task)
            for subtask in get_subtask_objs:
                db.delete(subtask)

            db.commit()

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def assign_task(assign_to, task_name):
    """
        It takes request and parameters and assigns
        a task
        :param assign_to: The name of the user to be assigned task
        :param task_name: The name of the task
        :return: A Response Object.
    """
    try:
        task = db.query(Task).filter(Task.task_name == task_name).first()

        # checks if assignee is also a user
        assignee = db.query(User).filter(User.username == assign_to).first()

        if task and assignee:
            # return jsonify({'message': 'Task or User not found'}), 404

            task_to_assign = AssignedTasks(user_id=assignee.id,
                                           task_id=task.id
                                           )
            db.add(task_to_assign)
            db.commit()

            task.assigned_users.append(assignee)
            assignee.assigned_tasks.append(task)

            db.add(task)
            db.add(assignee)

            db.commit()
            return jsonify(message=f'Task assigned to user {assign_to}'), 200
        return jsonify({'message': 'Task or assignee not found'}), 404

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=f"Task previously assigned to user {assign_to}",
                       ), status.HTTP_400_BAD_REQUEST


def unassign_task(unassigned_from, task_name):
    """
        It takes request and parameters and unassign
        a task
        :param unassigned_from: The name of the user to be unassigned task
        :param task_name: The name of the task
        :return: A Response Object.
    """
    try:
        task = db.query(Task).filter(Task.task_name == task_name).first()
        assignee = db.query(User).filter(User.username == unassigned_from).first()

        if not task or not assignee:
            return jsonify({'message': 'Task or assigned user not found'}), 404

        db.query(AssignedTasks).filter(AssignedTasks.user_id ==
                                       assignee.id,
                                       AssignedTasks.task_id == task.id).delete()
        db.commit()
        # and remove user from assigned_users list in  tasks table
        if assignee in task.assigned_users:
            task.assigned_users.remove(assignee)
            db.add(task)
            db.commit()

        return jsonify({'message': 'Task unassigned from user'}), 200

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def show_assigned_tasks(assignee):
    """
        It takes request and a parameter and retrieves
        all assigned tasks for a user
        :param assignee: The name of the user with assigned tasks
        :return: A Response Object.
    """
    assignee_account = db.query(User).filter(User.username == assignee).first()

    if assignee_account:
        get_assigned_tasks = assignee_account.assigned_tasks

        # Convert assigned tasks to a list of dictionaries for easy serialization
        task_list = [task.to_dict() for task in get_assigned_tasks]

        # Return the list of assigned tasks in the response
        return jsonify(assigned_to=assignee, assigned_tasks=task_list), status.HTTP_200_OK
    return jsonify(message="Assignee account not found"), status.HTTP_404_NOT_FOUND


# view assigned users

def show_assigned_users(task_name):
    """
        It takes request and a parameter and retrieves
        all assigned user for a task
        :param task_name: The name of the task
        :return: A Response Object.
    """
    # Retrieve all assigned users for a task
    task_assigned = db.query(Task).filter(Task.task_name == task_name).first()

    if task_assigned:
        # Return the list of assigned users in task in the response
        users_assigned = task_assigned.assigned_users
        get_assignees = [user.to_dict() for user in users_assigned if user is not None]

        return jsonify(task_name=task_name,
                       assigned_users=get_assignees), status.HTTP_200_OK

    return jsonify(message=f"No assigned user found for {task_name}"), status.HTTP_404_NOT_FOUND
